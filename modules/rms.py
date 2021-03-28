from modules.common.module import BotModule
import random

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.quotes = set()

    def get_settings(self):
        data = super().get_settings()
        data['quotes'] = list(self.quotes)
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('quotes'):
            self.quotes = set(data['quotes'])

    async def matrix_message(self, bot, room, event):
        self.logger.info(f"room: {room.name} sender: {event.sender} wants an rms quote")

        args = event.body.split()
        args.pop(0)

        try:
            cmd = args[0]
        except (ValueError,IndexError):
            cmd = ''

        if cmd == '!list':
            bot.must_be_owner(event)

            await bot.send_text(room, '\n'.join(self.quotes))

        elif cmd == '!add':
            bot.must_be_owner(event)
            args.pop(0)

            body = ' '.join(args)
            self.quotes.add(body)
            bot.save_settings()
            await bot.send_text(room, f'Added {body}.')

        elif cmd == '!remove':
            bot.must_be_owner(event)
            args.pop(0)
            l = list(self.quotes)

            for arg in args:
                l = [s for s in l if arg in s]
            if len(l) == 0:
                criteria = ' '.join(args)
                await bot.send_text(room, f'No quote found matching {criteria}')
            elif len(l) > 1:
                await bot.send_text(room, 'Multiple quotes found:\n{}'.format('\n'.join(l)))
            else:
                quote = l[0]
                self.quotes.remove(quote)
                bot.save_settings()
                await bot.send_text(room, f'Removed: {quote}')

        else:
            l = self.quotes
            for arg in args:
                l = set([s for s in l if arg in s])
            if len(l) == 0:
                criteria = ' '.join(args)
                await bot.send_text(room, f'No quote found matching {criteria}')
            else:
                quote = random.sample(l, 1)[0]
                await bot.send_text(room, f'"{quote}"', msgtype='m.text')

    def help(self):
        return 'Print an rms quote'
