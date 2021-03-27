from modules.common.module import BotModule


class MatrixModule(BotModule):
    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        args.pop(0)
        if len(args) == 0:
            target = event.sender
        else:
            target = ' '.join(args)
        self.logger.debug(f"room: {room.name} sender: {event.sender} asked for bacon")
        await bot.send_text(room, f"gives {target} a strip of bacon", msgtype="m.emote")

    def help(self):
        return 'Ask for a strip of bacon'
