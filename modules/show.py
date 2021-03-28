
from modules.common.module import BotModule

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.suggestions = dict()
        self.show = None
        self.is_live = False

    def get_settings(self):
        data = super().get_settings()
        data['suggestions'] = self.suggestions
        data['show'] = self.show
        data['is_live'] = self.is_live
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('suggestions'):
            self.suggestions = data['suggestions']
        if data.get('show'):
            self.show = data['show']
        if data.get('is_live'):
            self.is_live = data['is_live']

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

        if cmd in ['start', 'startshow', 'show']:
            bot.must_be_owner(event)
            if self.is_live:
                await bot.send_text(room, f'{self.show} is already live!')
            elif args:
                self.logger.info(f"room: {room.name} sender: {event.sender} is starting a show")
                self.show = ' '.join(args) or self.show

                await bot.send_text(room, 'Starting {self.show}!')
                self.suggestions = dict()
                bot.save_settings()

        elif cmd in ['end', 'endshow']:
            bot.must_be_owner(event)
            if self.is_live:
                self.logger.info(f"room: {room.name} sender: {event.sender} is ending a show")
                await bot.send_text(room, 'Ending {self.show}!')
                msg = self.make_poll()
                await bot.client.room_send(room.room_id, 'm.room.message', msg)
                bot.save_settings()
            else:
                await bot.send_text(room, 'No show is live!'.format(' '.join(args)))

        elif cmd in ['live']:
            self.logger.info(f"room: {room.name} sender: {event.sender} is asking if a show is live")
            if self.is_live:
                await bot.send_text(room, f'{self.show} is live!')
            else:
                await bot.send_text(room, 'No show is live!'.format(' '.join(args)))

        elif cmd in ['suggest']:
            if self.is_live:
                title = ' '.join(args[1:])
                self.logger.info(f"room: {room.name} sender: {event.sender} is suggesting {title}")
                if name := self.suggestions.get(title):
                    await bot.send_text(room, f'{title} was already suggested by {name}!')
                else:
                    self.suggestions[title] = event.sender
                    bot.save_settings()
            else:
                await bot.send_text(room, 'No show is live!')

    def make_poll(self):
        label = f'Title suggestions for {self.show}'
        options = []
        for i, k in enumerate(self.suggestions):
            s = '{} (from {})'.format(k, self.suggestions[k])
            options.append({
                'label': s,
                'value': '{}: {}'.format(i, s)
            })

        return {
            'body': label + '\n'.join([opt['label'] for opt in options]),
            'label': label,
            'msgtype': 'org.matrix.options',
            'options': options
        }

    def help(self):
        return 'Commands for a show'
