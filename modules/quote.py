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
        self.add_module_aliases(bot, *self.quotes.keys(), *self.aliases.keys())

    async def matrix_message(self, bot, room, event):

        args = event.body.split()

        cmd = args.pop(0).lower()
        if cmd == f'!{self.name}':
            try:
                cmd = args.pop(0).lower()
            except (ValueError,IndexError):
                cmd = '!'
        if cmd[0] == '!':
            cmd = cmd[1:]

        if cmd == 'wipeallquotes':
            bot.must_be_owner(event)
            self.logger.info(f"room: {room.name} sender: {event.sender} is wiping all quotes")
            self.quotes = {}
            self.aliases = {}

            bot.save_settings()
            await bot.send_text(room, 'Removed all quotes!')

        elif cmd in ['addname', 'addkey']:
            bot.must_be_owner(event)
            args.pop(0)
            args = [s.lower() for s in args]

            if len(args) != 1:
                await bot.send_text(room, f'{cmd} takes exactly one argument')
            elif self.key_exists(args[0]):
                await bot.send_text(room, '{} already exists'.format(args[0]))
            else:
                self.logger.info(f"room: {room.name} sender: {event.sender} is adding a key")
                key = args[0].lower()
                self.quotes[key] = []
                self.add_module_aliases(bot, key)
                bot.save_settings()
                await bot.send_text(room, 'Added {}'.format(args[0]))


        elif cmd in ['addalias', 'alias']:
            bot.must_be_owner(event)
            args.pop(0)
            args = [s.lower() for s in args]

            if len(args) != 2:
                await bot.send_text(room, f'{cmd} takes exactly two arguments')
            elif self.key_exists(args[0]):
                await bot.send_text(room, '{} already exists'.format(args[0]))
            else:
                if self.aliases.get(args[1]):
                    args[1] = self.aliases[args[1]]
                if self.quotes.get(args[1]) is not None:
                    self.logger.info(f"room: {room.name} sender: {event.sender} is adding an alias")
                    self.aliases[args[0].lower()] = args[1].lower()
                    bot.save_settings()
                    await bot.send_text(room, 'Added {} as alias for {}'.format(args[0], args[1]))
                else:
                    await bot.send_text(room, 'No such name: {}'.format(args[1]))

        elif cmd in ['list', 'ls', 'l']:
            bot.must_be_owner(event)
            args.pop(0)

            self.logger.info(f"room: {room.name} sender: {event.sender} wants to list quotes")
            if len(args) == 0:
                await bot.send_text(room, '\n'.join(self.quotes.keys()))
            else:
                try:
                    await bot.send_text(room, '\n'.join(self.get_quotes(*args)))
                except:
                    await bot.send_text(room, 'No matching quote')

        elif cmd in ['add', 'a', 'new']:
            bot.must_be_owner(event)
            args.pop(0)

            try:
                key = args.pop(0)
                body = ' '.join(args)
                self.add_quote(key, body)
                bot.save_settings()
                await bot.send_text(room, f'Added to {key} quotes: {body}.')
            except IndexError:
                await bot.send_text(room, f'{cmd} requires a key and a quote')
            except KeyError:
                await bot.send_text(room, f'{key} does not exist')


        elif cmd in ['remove', 'rm', 'r']:
            bot.must_be_owner(event)
            args.pop(0)

            try:
                key = args.pop(0)
                quotes = self.quotes[self.aliases.get(key) or key]
                l = self.get_quotes(key, *args)
                if len(l) == 0:
                    await bot.send_text(room, 'No matching quote')
                elif len(l) > 1:
                    await bot.send_text(room, 'Multiple quotes found:\n - {}'.format('\n - '.join(l)))
                else:
                    quotes.remove(l[0])
                    bot.save_settings()
                    self.logger.info(f"room: {room.name} sender: {event.sender} is removing a quote")
                    await bot.send_text(room, 'Removed quote: {}'.format(l[0]))
            except KeyError:
                await bot.send_text(room, 'No such key: {}'.format(args[0]))

        else:
            if not cmd in ['get']:
                # push cmd back into list
                args.insert(0, cmd)
            self.logger.info(f"room: {room.name} sender: {event.sender} wants a quote")
            try:
                quote = random.sample(self.get_quotes(*args), 1)[0]
                await bot.send_text(room, f'"{quote}"', msgtype='m.text')
            except TypeError:
                await bot.send_text(room, 'Missing argument')
            except ValueError:
                await bot.send_text(room, 'No such quote found')
            except KeyError:
                await bot.send_text(room, 'Not a valid key: {}. Try using "any" as a key.'.format(args[0]))

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
        return 'Print an rms quote'
