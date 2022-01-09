from modules.common.module import BotModule
import random
import html

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.rooms = dict()

    def get_settings(self):
        data = super().get_settings()
        data['rooms'] = self.rooms
        return data

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('rooms'):
            self.rooms = data['rooms']

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, ['spin'])

    async def matrix_message(self, bot, room, event):

        args = event.body.split()

        cmd = args.pop(0).lower()
        if cmd == f'!{self.name}' and len(args):
            cmd = args.pop(0).lower()
        if cmd[0] == '!':
            cmd = cmd[1:]

        if cmd in ['setup', 'wheelsetup']:
            bot.must_be_admin(room, event)
            if room.room_id in self.rooms.keys():
                return

            self.logger.info(f"Allowing !wheel in {room.name}")
            self.rooms[room.room_id] = dict()
            bot.save_settings()
            return

        if not room.room_id in self.rooms:
            return

        wheel = self.rooms[room.room_id]

        if cmd in ['list', 'ls']:
            bot.must_be_admin(room, event)
            wheel = wheel.values()
            return await bot.send_html(room,
                    '\n'.join(map(lambda x: f'<b>{html.escape(x[0])}</b> ({html.escape(x[1])})', wheel)),
                    '\n'.join(map(lambda x: f'{x[0]} ({x[1]})', wheel))
            )

        if cmd in ['spin']:
            bot.must_be_admin(room, event)
            self.logger.info(f"room: {room.name} sender: {event.sender} is spinning the wheel")
            try:
                entry = wheel.pop(random.choice(list(wheel.keys())))
                res   = await bot.send_html(room,
                        f'<b>{html.escape(entry[0])}</b> (suggested by {html.escape(entry[1])})',
                        f'{entry[0]} (suggested by {entry[1]})',
                        msgtype='m.text'
                )
                bot.save_settings()
                return res
            except ValueError:
                return await bot.send_text(room, 'The wheel is empty! Try "!wheel add <something>" first.')
            except KeyError:
                return await bot.send_text(room, 'Not a valid key: {}. Try using "any" as a key.'.format(cmd))

        if cmd in ['add', 'suggest']:
            title = ' '.join(args)
            key   = title.lower()
            if wheel.get(key):
                return await bot.send_msg(event.sender,
                        f'Private message from {bot.matrix_user}',
                        f'{title} already suggested!')
            self.logger.info(f"room: {room.name} sender: {event.sender} is suggesting {title}")
            wheel[key] = (title, event.sender)
            return await bot.send_msg(event.sender,
                    f'Private message from {bot.matrix_user}',
                    f'Suggested {title}')
            bot.save_settings()

    def help(self):
        return 'Suggest an entry for the wheel'
