from modules.common.module import BotModule
from bs4 import BeautifulSoup
from html import escape
from subprocess import Popen, PIPE

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.langmap = {}

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('langmap'):
            self.langmap = data['langmap']

    def get_settings(self):
        data = super().get_settings()
        data['langmap'] = self.langmap
        return data

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, [*self.langmap.keys()])

    async def matrix_message(self, bot, room, event):

        body = event.body
        try:
            cmd, body = body.split(None, 1)
            if cmd in ['!' + self.name, self.name]:
                cmd, body = body.split(None, 1)
        except ValueError:
            cmd = body.strip()
            body = ''
        cmd = cmd.lstrip('!')

        if cmd in ['addlang', 'add', 'newlang', 'new']:
            bot.must_be_owner(event)
            self.logger.info(f"room: {room.name} sender: {event.sender} wants to add a language")
            args = body.split()

            if len(args) < 2:
                await bot.send_text(room, f'{cmd} takes two arguments!')
            elif args[0] in self.langmap.keys():
                await bot.send_text(room, f'{args[0]} already exists')
            else:
                self.logger.info(f"room: {room.name} sender: {event.sender} is adding a language")
                key = args[0].lower()
                self.langmap[key] = {"container": args[1], "command": args[2:]}
                bot.save_settings()
                await bot.send_text(room, 'Added {}'.format(args[0]))

        elif cmd in ['set', 'property', 'setprop', 'setproperty']:
            bot.must_be_owner(event)
            self.logger.info(f"room: {room.name} sender: {event.sender} wants to modify a language")
            args = body.split()

            if len(args) < 3:
                await bot.send_text(room, f'Usage: {cmd} [lang] [property] [value ...].')
                return
            lang = self.get_lang(args[0])
            if not lang:
                await bot.send_text(room, f'{lang} has not been added.')
                return

            # integer values
            if args[1] in ['timeout']:
                val = int(args[2])
                if val <= 0:
                    await bot.send_text(room, f'{args[1]} must be a positive integer')
                    return
            # string values
            elif args[1] in ['container']:
                val = args[2]
            # list values
            elif args[1] in ['podman_opts', 'command']:
                val = args[2:]
            # unknown values
            else:
                await bot.send_text(room, f'Not a property: {args[1]}')
                return

            lang[args[1]] = val
            bot.save_settings()
            await bot.send_text(room, f'Set property {args[1]} for {args[0]}')


        else:
            self.logger.info(f"room: {room.name} sender: {event.sender} wants to eval some code")

            lang, code  = self.get_code(event.formatted_body)
            # !eval [lang]
            lang = self.get_lang(cmd) or lang
            html, plain = self.run_code(lang, code)
            await bot.send_html(room, html, plain)

    def get_code(self, html_body):
        blocks = BeautifulSoup(html_body, features='html.parser').find_all('code')
        if not blocks:
            return None
        for block in blocks:
            c = block.get('class')
            if not c:
                continue
            lang = self.get_lang(c[0])
            if lang:
                break
        else:
            block = blocks[0]
            lang = None
        return (lang, block.contents[0].string)

    def get_lang(self, s):
        # Python 3.9
        return self.langmap.get(s.removeprefix('language-'))

    def run_code(self, lang, code, podman_opts=[], timeout=15):
        container = lang['container']
        cmd = lang['command']
        self.logger.info(f"Running in podman {container} with {cmd}")

        timeout = lang.get('timeout') or timeout
        podman_opts = lang.get('podman_opts') or podman_opts

        proc = Popen(['podman', 'run', '--rm', '-i', '--net=none', '--workdir=/root']
            + podman_opts + [container] + cmd,
            stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate(input=code.encode('utf-8'), timeout=timeout)
        return ('\n'.join(i) for i in
            zip(self.code_block('stdout', stdout.decode()), self.code_block('stderr', stderr.decode()))
        )

    def code_block(self, header, text):
        if text:
            return (
                f'<p><strong>{escape(header)}: </strong></p><pre><code class="language-txt">'
                + escape(text) + '</code></pre>',
                # use markdown-style blocks for clients which parse it from event.body
                '\n'.join([header, '```', text.rstrip(), '```'])
            )
        else:
            return (f'<p><em>no {escape(header)}</em>', f'(no {header})')

    def help(self):
        return 'Evaluate code blocks or !addlang [image] [cmd ...]'
