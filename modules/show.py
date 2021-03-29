
from modules.common.module import BotModule

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

        # This room's show data
        try: 
            show = self.rooms[room.room_id]
        except:
            if bot.is_owner(event):
                self.logger.info(f"No show data for {room.name}, creating defaults")
                self.rooms[room.room_id] = {
                        'title': room.name,
                        'is_live': False,
                        'suggestions': dict()
                }
                bot.save_settings()
                show = self.rooms[room.room_id]
            else:
                return

        if cmd in ['help', '-help', '--help']:
            self.logger.info(f"room: {room.name} sender: {event.sender} asked for show help")

            bot.send_msg(
                    event.sender,
                    'Chat with ' + bot.matrix_user,
                    self.long_help(*args, is_owner=bot.is_owner(event))
            )

        elif cmd in ['name', 'rename', 'nameshow', 'renameshow']:
            bot.must_be_owner(event)

            self.logger.info(f"room: {room.name} sender: {event.sender} wants to rename a show")
            self.set_title(show, ' '.join(args))
            bot.save_settings()

        elif cmd in ['begin', 'beginshow', 'start', 'startshow']:
            bot.must_be_owner(event)

            self.set_title(show, ' '.join(args))
            title = self.get_title(show, room)

            self.logger.info(f"room: {room.name} sender: {event.sender} wants to start a show")
            if show['is_live']:
                await bot.send_text(room, f'{title} is already live!')
            else:
                self.logger.info(f"room: {room.name} sender: {event.sender} is starting a show")

                await bot.send_text(room, f'Starting {title}!')

                show['is_live'] = True
                show['suggestions'] = dict()
                bot.save_settings()

        elif cmd in ['end', 'endshow', 'stop', 'stopshow']:
            bot.must_be_owner(event)

            title = self.get_title(show, room)
            if show['is_live']:
                self.logger.info(f"room: {room.name} sender: {event.sender} is ending a show")
                await bot.send_text(room, f'Ending {title}!')
                show['is_live'] = False
                msg = self.make_poll(show)
                await bot.client.room_send(room.room_id, 'm.room.message', msg)
                bot.save_settings()
            else:
                await bot.send_text(room, 'No show is live!')

        elif cmd in ['suggest']:
            if show['is_live']:
                title = ' '.join(args)
                self.logger.info(f"room: {room.name} sender: {event.sender} is suggesting {title}")
                other_user = show['suggestions'].get(title)
                if other_user:
                    await bot.send_text(room, f'{title} was already suggested by {other_user}!')
                else:
                    show['suggestions'][title] = event.sender
                    bot.save_settings()
            else:
                await bot.send_text(room, 'No show is live!')

        # For now, consider "live" as default
        #elif cmd in ['live', 'islive']:
        else:
            self.logger.info(f"room: {room.name} sender: {event.sender} is asking if a show is live")
            if show['is_live']:
                title = self.get_title(show, room)
                await bot.send_text(room, f'{title} is live!')
            else:
                await bot.send_text(room, 'No show is live!')


    def make_poll(self, show):
        title = show['title']
        label = f'Title suggestions for {title}'
        options = []
        for i, k in enumerate(show['suggestions']):
            s = '{} ({})'.format(k, show['suggestions'][k])
            options.append({
                'label': s,
                'value': '{}: {}'.format(i, s)
            })

        return {
            'body': label + '\n' + '\n'.join([opt['label'] for opt in options]),
            'label': label,
            'msgtype': 'org.matrix.options',
            'type': 'org.matrix.poll',
            'options': options
        }

    def set_title(self, show, title):
        if title:
            show['title'] = title

    # Fallback show title
    def get_title(self, show, room):
        return show['title'] or self[room.name]

    def help(self):
        return 'Commands for a show'

    def long_help(self, *args, is_owner=False, is_admin=False):
        text = [
            'Usage: !show [cmd]',
            '- !show help: Message you this help text',
            '- !show live: Ask if a show is live for the current room',
            '- !show suggest [your cool title]: Suggest a title for the current show'
        ]
        if is_owner:
            text += [
                '- !show (re)name [new show name]: Rename the show for the current room',
                '- !show start[[new show name]]: Start the show for the current room',
                '   Optional argument renames the show',
                '- !show stop | !show end: Ends the currently running show',
            ]
        return '\n'.join(text)
