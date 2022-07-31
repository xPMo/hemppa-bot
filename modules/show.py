
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

    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.add_module_aliases(bot, ['suggest', 'live'])

    async def matrix_message(self, bot, room, event):

        args = event.body.split()
        cmd = args.pop(0).lower()
        if cmd == f'!{self.name}' and len(args):
            cmd = args.pop(0).lower()
        if cmd[0] == '!':
            cmd = cmd[1:]
        if cmd in ['setup']:
            bot.must_be_admin(room, event)

            self.logger.info(f"Reset all data relating to a show in this room")
            self.rooms[room.room_id] = {
                    'title': ' '.join(args) or room.name,
                    'is_live': False,
                    'suggestions': dict()
            }
            bot.save_settings()
            show = self.rooms[room.room_id]
            return

        # This room's show data
        try: 
            show = self.rooms[room.room_id]
        except:
            # ignore !show commands
            return

        if cmd in ['help']:
            self.logger.info(f"room: {room.name} sender: {event.sender} asked for show help")
            return await bot.send_text(room, self.long_help(bot=bot, room=room, event=event, args=([cmd] + args)), event=event)

        elif cmd in ['name', 'rename', 'nameshow', 'renameshow']:
            bot.must_be_admin(room, event)

            self.logger.info(f"room: {room.name} sender: {event.sender} wants to rename a show")
            self.set_title(show, ' '.join(args))
            bot.save_settings()

        elif cmd in ['begin', 'beginshow', 'start', 'startshow']:
            bot.must_be_admin(room, event)

            self.set_title(show, ' '.join(args))
            title = self.get_title(show, room)

            self.logger.info(f"room: {room.name} sender: {event.sender} wants to start a show")
            if show['is_live']:
                await bot.send_text(room, f'{title} is already live!', event=event)
            else:
                self.logger.info(f"room: {room.name} sender: {event.sender} is starting a show")

                await bot.send_text(room, f'Starting {title}!', event=event)

                show['is_live'] = True
                show['suggestions'] = dict()
                bot.save_settings()

        elif cmd in ['end', 'endshow', 'stop', 'stopshow']:
            bot.must_be_admin(room, event)

            title = self.get_title(show, room)
            if show['is_live']:
                self.logger.info(f"room: {room.name} sender: {event.sender} is ending a show")
                await bot.send_text(room, f'Ending {title}!', event=event)
                show['is_live'] = False
                msg = self.make_poll(show)
                await bot.client.room_send(room.room_id, 'org.matrix.msc3381.poll.start', msg)
                bot.save_settings()
            else:
                await bot.send_text(room, 'No show is live!', event=event)

        elif cmd in ['suggest']:
            if not show['is_live']:
                return await bot.send_text(room, 'No show is live!', event=event)
            title = ' '.join(args)
            self.logger.info(f"room: {room.name} sender: {event.sender} is suggesting {title}")
            other_user = show['suggestions'].get(title)
            if other_user:
                return await bot.send_text(room, f'{title} was already suggested by {other_user}!', event=event)
            show['suggestions'][title] = event.sender
            bot.save_settings()
            return await bot.room_send(room.room_id, event, 'm.reaction', self.react(event, '✅'))

        # For now, consider "live" as default
        #elif cmd in ['live', 'islive']:

        else:
            self.logger.info(f"room: {room.name} sender: {event.sender} is asking if a show is live")
            if show['is_live']:
                title = self.get_title(show, room)
                await bot.send_text(room, f'{title} is live!', event=event)
            else:
                await bot.send_text(room, 'No show is live!', event=event)


    def make_poll(self, show):
        title = show['title']
        label = f'Title suggestions for {title}'
        options = []
        for i, k in enumerate(show['suggestions']):
            s = '{} ({})'.format(k, show['suggestions'][k])
            options.append({
                'id': f'{i}-{s}',
                'org.matrix.msc1767.text': s
            })

        return {
            'org.matrix.msc1767.text': '\n'.join(
                [label] + [opt['org.matrix.msc1767.text'] for opt in options]
            ),
            'org.matrix.msc3381.poll.start': {
                'question': {
                    'org.matrix.msc1767.text': label,
                    'body': label,
                    'msgtype': 'm.text'
                },
                'kind': 'org.matrix.msc3381.poll.disclosed',
                'answers': options,
                'max_selections': i
            }
        }

    def set_title(self, show, title):
        if title:
            show['title'] = title

    def react(self, event, reaction):
        return {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": event.event_id,
                "key": reaction
            }
        }

    # Fallback show title
    def get_title(self, show, room):
        return show['title'] or self[room.name]

    def help(self):
        return 'Commands for a show'

    def long_help(self, bot=None, room=None, event=None, **kwargs):
        text = [
            self.help(),
            '- !show help: Reply with this help text',
            '- !show live: Ask if there is a show live in the current room',
            '- !show suggest [your cool title]: Suggest a title for the current show'
        ]
        if bot and room and event and bot.is_admin(room, event):
            text += [
                'Admin commands:',
                '- !show (re)name [new show name]: Rename the show for the current room',
                '- !show start [[new show name]]: Start the show for the current room',
                '   Optional argument renames the show',
                '- !show (stop|end): Ends the currently running show',
            ]
        return '\n'.join(text)
