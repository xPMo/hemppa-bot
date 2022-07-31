from modules.common.module import BotModule
from nio import RoomMessageText

import shlex
from bs4 import BeautifulSoup
from html import escape

from subprocess import run, PIPE, TimeoutExpired

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.langmap  = dict()
        self.aliases  = dict()
        self.commands = {
                **dict.fromkeys(['add', 'new', 'addlang', 'newlang'], self.add_lang),
                **dict.fromkeys(['rm', 'remove', 'rmlang', 'delete'], self.rm_lang),
                **dict.fromkeys(['alias', 'aliaslang'], self.alias_lang),
                **dict.fromkeys(['set', 'setlang', 'setprop'], self.set_lang_prop),
                **dict.fromkeys(['get', 'getlang', 'getprop'], self.get_lang_prop),
                **dict.fromkeys(['list', 'ls', 'langs'], self.list_langs),
                **dict.fromkeys(['run'], self.cmd_code),
        }

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('langmap'):
            self.langmap = data['langmap']
        if data.get('aliases'):
            self.aliases = data['aliases']

    def get_settings(self):
        data = super().get_settings()
        data['langmap'] = self.langmap
        data['aliases'] = self.aliases
        return data

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot
        bot.client.add_event_callback(self.message_cb, RoomMessageText)
        langs = [*self.aliases.keys(), *self.langmap.keys()]
        self.add_module_aliases(bot, langs + [f'eval{key}' for key in langs])

    def matrix_stop(self, bot):
        super().matrix_stop(bot)
        bot.remove_callback(self.message_cb)

    async def add_lang(self, bot, room, event, cmd):
        bot.must_be_owner(event)
        self.logger.info(f"sender: {event.sender} wants to add a language")
        args = shlex.split(event.body)

        key = args[0].lower()
        if len(args) < 3:
            return await bot.send_text(room, f'{cmd} needs at least three arguments', event)

        if key in self.langmap.keys():
            return await bot.send_text(room, f'{args[0]} already exists', event)

        self.logger.info(f"sender: {event.sender} is adding a language")
        self.langmap[key] = {"container": args[1], "command": args[2:]}
        self.add_module_aliases(bot, [key, f'eval{key}'])
        bot.save_settings()
        return await bot.send_text(room, f'Added {args[0]}', event=event)

    async def rm_lang(self, bot, room, event, cmd):
        bot.must_be_owner(event)
        self.logger.info(f"sender: {event.sender} wants to remove a language")
        args = event.body.split()

        if len(args) != 1:
            return await bot.send_text(room, f'{cmd} takes exactly one arguments', event)

        try:
            self.langmap.pop(args[0])
            self.aliases = {k:v for k, v in self.aliases.items() if v != args[0]}
            bot.save_settings()
            return await bot.send_text(room, f'removed language {args[0]}', event)
        except KeyError:
            pass
        try:
            self.aliases.pop(args[0])
            bot.save_settings()
            return await bot.send_text(room, f'removed alias {args[0]}', event)
        except:
            return await bot.send_text(room, f'No language or alias found', event)

    async def list_langs(self, bot, room, event, cmd):
        ret = {k: None for k in self.langmap.keys()}
        for k, v in self.aliases.items():
            if ret[v]:
                ret[v].append(k)
            else:
                ret[v] = [k]
        await bot.send_text(room, '\n'.join([f'{k}: ({", ".join(v)})' if v else k for k, v in ret.items()]), event)

    async def alias_lang(self, bot, room, event, cmd):
        bot.must_be_owner(event)
        self.logger.info(f"sender: {event.sender} wants to alias a language")
        args = event.body.split()

        if len(args) < 2:
            msg = f'{cmd} takes two arguments'

        args = [arg.lower() for arg in args]
        if args[0] in self.langmap.keys():
            msg = f'Already a language: {args[0]}'

        if not args[1] in self.langmap.keys():
            msg = f'Not a language: {args[1]}'

        self.aliases[args[0]] = args[1]
        self.add_module_aliases(bot, [args[0], f'eval{args[0]}'])
        bot.save_settings()
        return await bot.send_text(room, f'Added {args[0]}', event)

    async def set_lang_prop(self, bot, room, event, cmd):
        bot.must_be_owner(event)
        self.logger.info(f"sender: {event.sender} wants to modify a language")
        args = shlex.split(event.body)

        if len(args) < 3:
            return await bot.send_text(room, f'Usage: {cmd} [lang] [property] [value ...].', event)
        lang = self.get_lang(args[0])
        if not lang:
            return await bot.send_text(room, f'{lang} has not been added.', event)

        # integer values
        if args[1] in ['timeout']:
            val = int(args[2])
            if val <= 0:
                return await bot.send_text(room, f'{args[1]} must be a positive integer', event)
        # string values
        elif args[1] in ['container', 'memory', 'pids', 'net', 'workdir', 'stdout-class', 'stdin-class']:
            val = args[2]
        # list values
        elif args[1] in ['podman_opts', 'command']:
            val = args[2:]
        # unknown values
        else:
            return await bot.send_text(room, f'Not a property: {args[1]}', event)

        lang[args[1]] = val
        bot.save_settings()
        return await bot.send_text(room, f'Set property {args[1]} for {args[0]}', event)

    async def get_lang_prop(self, bot, room, event, cmd):
        self.logger.info(f"sender: {event.sender} wants to list a language's properties")
        name = event.body.split(None, 1)[0]
        lang = self.get_lang(name)
        if not lang:
            msg = f'{lang} has not been added.'
        else:
            msg = '\n'.join([f'{name}:'] + [f'- {k}: {v}' for k, v in lang.items()])
        await bot.send_text(room, msg, event)

    async def cmd_code(self, bot, room, event, cmd):
        lang = None
        try:
            self.logger.info(f"sender: {event.sender} wants to eval some code")
            lang, code = self.get_code_html(event.formatted_body)
            lang = self.get_lang(cmd) or lang
        except (AttributeError, TypeError):
            # No formatted_body
            code = event.body
            lang = self.get_lang(cmd) or lang
        if not lang:
            return await bot.send_text(room, f'No matching language', event)
        html, plain = self.run_code(lang, code, f'eval-{event.sender}')
        return await bot.send_html(room, html, plain, event)

    async def message_cb(self, room, event):
        """
        Handle client callbacks for all room text events
        """
        if self.bot.should_ignore_event(event):
            return

        content = event.source.get('content')
        if not content:
            return

        # Don't re-run edited messages
        if "m.new_content" in content:
            return
        try:
            if not event.formatted_body:
                return
            # Make sure the class ends with '!'
            lang, code = self.get_code_html(event.formatted_body,
                    match_class=self.cb_match_class)
            if not lang:
                return
            self.logger.info(f"sender: {event.sender} wants to eval some code")
            html, plain = self.run_code(lang, code, f'eval-{event.sender}')
            return await self.bot.send_html(room, html, plain, event=event)
        except (ValueError, IndexError):
            return
        except Exception as e:
            # No formatted body
            self.logger.warning(f'unexpected exception in callback: {repr(e)}')

    async def matrix_message(self, bot, room, event):
        try:
            cmd, event.body = event.body.split(None, 1)      # [!cmd] [(!)subcmd body]
            if cmd in ['!' + self.name, self.name]:
                cmd, event.body = event.body.split(None, 1)  # [!subcmd] [body]
        except (ValueError, IndexError):
            # couldn't split, not enough arguments in body
            cmd = event.body.strip()
            event.body = ''
        cmd = cmd.lstrip('!')

        op = self.commands.get(cmd) or self.cmd_code
        await op(bot, room, event, cmd)

    def run_code(self, lang, code, label):
        container = lang['container']
        podman_cmd = lang['command']
        self.logger.info(f"Running in podman {container} with {podman_cmd}")
        podman_opts = [f'--label={label}']

        # set limits
        timeout = lang.get('timeout') or 15
        net = lang.get('net') or 'none'
        pids = lang.get('pids-limit') or 64
        mem = lang.get('memory') or '32M'
        workdir = lang.get('workdir') or '/root'

        podman_opts += [f'--pids-limit={pids}', f'--memory={mem}', f'--net={net}', f'--workdir={workdir}']
        podman_opts += lang.get('podman_opts') or []

        parts = []
        try:
            proc = run(['podman', 'run', '--rm', '-i'] + podman_opts + [container] + podman_cmd,
                input=code.encode('utf-8'), capture_output=True, timeout=timeout)
            stdout = proc.stdout
            stderr = proc.stderr
            if proc.returncode != 0:
                parts.append((
                    f'<p><strong>Process exited non-zero</strong>: <code>{proc.returncode}</code></p>',
                    f'(Process exited non-zero: {proc.returncode})'
                ))
        except TimeoutExpired as e:
            stdout = e.stdout
            stderr = e.stderr
            parts.append((
                f'<p><strong>Process timed out in {timeout}s</strong></p>',
                f'Process timed out in {timeout}s'
            ))

        stdout = stdout and self.code_block(lang.get('stdout-class'), stdout.decode().strip('\n'))
        stderr = stderr and self.code_block(lang.get('stderr-class'), stderr.decode().strip('\n'))
        if not stdout and not stderr:
            parts.append(('<p><em>no stdout or stderr</em></p>', 'no stdout or stderr'))
        else:
            parts += [stdout or ('<p><em>no stdout</em></p>', 'no stdout'), stderr or ('<p><em>no stderr</em></p>', 'no stderr')]

        return ('\n'.join(i) for i in zip(*parts))

    def get_code_html(self, html, match_class=None):
        lang   = None
        soup   = BeautifulSoup(html, features='html.parser')
        for block in soup.find_all('mx-reply'):
            block.decompose()
        soup.find
        blocks = soup.find_all('code')
        for block in blocks:
            clss = block.get('class')
            if not clss:
                continue
            for cls in block.get('class'):
                if match_class and not match_class(cls):
                    continue
                lang = self.get_lang(cls)
                if lang:
                    return (lang, block.contents[0].string)
        return (None, blocks[0].contents[0].string)

    def get_lang(self, name):
        # Python 3.9
        name = (name
            .removeprefix('language-')
            .removeprefix('!eval')
            .removeprefix('!')
            .removesuffix('!')
        )
        name = self.aliases.get(name) or name
        return self.langmap.get(name)

    def cb_match_class(self, s):
        return s.startswith('language-!') or s[-1] == '!'

    def code_block(self, langclass, text):
        if text:
            langclass = langclass or 'txt'
            return (
                f'<pre><code class="language-{langclass}">{escape(text)}</code></pre>',
                # use markdown-style blocks for clients which parse it from event.body
                '\n'.join(['```', text, '```'])
            )
        else:
            return None

    def help(self):
        return 'Evaluate code in an ephemeral container'

    def long_help(self, bot=None, event=None, **kwargs):
        text = self.help() + (
                '\n- !eval (list|ls|langs): list the current languages and their aliases'
                '\n- !eval (get|getprop) [lang]: get the current properties for the given language'
                '\n- !eval run [lang] [code]: run code (see below)'
                '\n- !eval[lang] [code]: run code (see below)'
                '\n- ![lang] [code]: run code (see below)'
                '\n- ... [marked-codeblock] ...: run code (see below)'
                )
        if bot and event and bot.is_owner(event):
            text += ('\nBot owner commands:'
                     '\n- !eval (add|new) [lang] [container] [command ...]: add an new language'
                     '\n- !eval alias [name] [lang]: add an alias [name] for [lang]'
                     '\n- !eval (set|setprop) [lang] [property] [value]: alter a language'
                     '\n- !eval (remove|rm) [name]: remove a language, or alias to a language'
                     )
        text += ('\nRunning code:'
                 '\n>  !eval will attempt to find a code block in the message\'s formatteed_body.'
                 '\n>  If a multiline codeblock has a language specifier, that language is preferred.'
                 '\n>  Otherwise, the first codeblock (inline or otherwise) is used'
                 'with the language given in one of the forms above.'
                 '\n>  If no codeblock is found, then the remaining body after [lang] is interpreted as code.'
                 '\nMarked codeblock:'
                 '\n>  A marked codeblock contains a formatted_body with a <code class="language-[lang]!"> block.'
                 '\n>  Your markdown editor can probably produce such a code block with ```[lang]!'
                 )
        return text
