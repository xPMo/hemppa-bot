from modules.common.module import BotModule
import random

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.quotes = {}
        self.aliases = {}
        self.wildcards = [None, 'any', '*', '']

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('aliases'):
            self.aliases = data['aliases']
        if data.get('quotes'):
            self.quotes = data['quotes']

    def get_settings(self):
        data = super().get_settings()
        data['quotes'] = self.quotes
        data['aliases'] = self.aliases
        return data

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, [*self.quotes.keys(), *self.aliases.keys()])

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

        if cmd == 'wipeallquotes':
            bot.must_be_owner(event)
            self.logger.info(f"room: {room.name} sender: {event.sender} is wiping all quotes")
            self.quotes = {}
            self.aliases = {}

            bot.save_settings()
            await bot.send_text(room, event, 'Removed all quotes!')

        elif cmd in ['addname', 'addkey']:
            bot.must_be_owner(event)
            args = body.split()

            if len(args) != 1:
                await bot.send_text(room, event, f'{cmd} takes exactly one argument')
            elif self.key_exists(args[0]):
                await bot.send_text(room, event, '{} already exists'.format(args[0]))
            else:
                self.logger.info(f"room: {room.name} sender: {event.sender} is adding a key")
                key = args[0].lower()
                self.quotes[key] = []
                self.add_module_aliases(bot, [key])
                bot.save_settings()
                await bot.send_text(room, event, 'Added {}'.format(args[0]))


        elif cmd in ['addalias', 'alias']:
            bot.must_be_owner(event)
            args = body.split()

            if len(args) != 2:
                await bot.send_text(room, event, f'{cmd} takes exactly two arguments')
            elif self.key_exists(args[0]):
                await bot.send_text(room, event, '{} already exists'.format(args[0]))
            else:
                if self.aliases.get(args[1]):
                    args[1] = self.aliases[args[1]]
                if self.quotes.get(args[1]) is not None:
                    self.logger.info(f"room: {room.name} sender: {event.sender} is adding an alias")
                    key = args[0].lower()
                    self.aliases[key] = args[1].lower()
                    self.add_module_aliases(bot, [key])
                    bot.save_settings()
                    await bot.send_text(room, event, 'Added {} as alias for {}'.format(args[0], args[1]))
                else:
                    await bot.send_text(room, event, 'No such name: {}'.format(args[1]))

        elif cmd in ['list', 'ls', 'l']:
            bot.must_be_owner(event)

            self.logger.info(f"room: {room.name} sender: {event.sender} wants to list quotes")
            if body:
                try:
                    await bot.send_text(room, event, '\n'.join(self.get_quotes(*body.split())))
                except:
                    await bot.send_text(room, event, 'No matching quote')
            else:
                await bot.send_text(room, event, '\n'.join(self.quotes.keys()))

        elif cmd in ['add', 'a', 'new']:
            bot.must_be_owner(event)

            try:
                key, body = body.split(None, 1)
                self.add_quote(key, body)
                bot.save_settings()
                await bot.send_text(room, event, f'Added to {key} quotes: {body}.')
            except IndexError:
                await bot.send_text(room, event, f'{cmd} requires a key and a quote')
            except KeyError:
                await bot.send_text(room, event, f'{key} does not exist')


        elif cmd in ['remove', 'rm', 'r']:
            bot.must_be_owner(event)

            try:
                args = body.split()
                quotes = self.quotes[args[0]]

                l = self.get_quotes(*args)
                if len(l) == 0:
                    await bot.send_text(room, event, 'No matching quote')
                elif len(l) > 1:
                    await bot.send_text(room, event, 'Multiple quotes found:\n - {}'.format('\n - '.join(l)))
                else:
                    quotes.remove(l[0])
                    bot.save_settings()
                    self.logger.info(f"room: {room.name} sender: {event.sender} is removing a quote")
                    await bot.send_text(room, event, 'Removed quote: {}'.format(l[0]))
            except KeyError:
                await bot.send_text(room, event, 'No such key: {}'.format(args[0]))

        else:

            self.logger.info(f"room: {room.name} sender: {event.sender} wants a quote")
            try:
                quote = random.sample(self.get_quotes(cmd, *body.split()), 1)[0]
                await bot.send_text(room, event, f'{quote}', msgtype='m.text')
            except TypeError:
                await bot.send_text(room, event, 'Missing argument')
            except ValueError:
                await bot.send_text(room, event, 'No such quote found')
            except KeyError:
                await bot.send_text(room, event, 'Not a valid key: {}. Try using "any" as a key.'.format(cmd))

    def get_quotes(self, key, *criteria):
        """Returns a list of quotes which contains all strings from criteria

        If key is None, "any", or "*", quotes from all keys will be returned.
        Otherwise, this may throw a KeyError if the key does not exist.
        """
        key = key.lower()
        if key in self.wildcards:
            quotes = sum(list(self.quotes.values()), [])
        else:
            quotes = list(self.quotes[self.aliases.get(key) or key])
        for criterion in criteria:
            quotes = [q for q in quotes if criterion in q]
        return quotes

    def add_quote(self, key, quote):
        key = key.lower()
        key = self.aliases.get(key) or key
        if quote in self.quotes[key]:
            pass
        self.quotes[key].append(quote)

    def key_exists(self, key):
        key = key.lower()
        return key in self.wildcards or key in self.aliases.keys() or key in self.quotes.keys()

    def help(self):
        return 'Print or manage quotes (add, remove, addname, addalias)'
