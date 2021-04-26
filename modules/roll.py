from modules.common.module import BotModule
from random import randrange

class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        self.logger.info(f"room: {room.name} sender: {event.sender} is rolling dice")
        try:
            args = event.body.split()[1:]
            res = []
            for arg in args:
                count, sides = arg.split('d')
                sides = int(sides)
                count = int(count or 1)
                res += [1 + randrange(sides) for _ in range(count)]
            await bot.send_text(room, f'{event.sender}: {"+".join(map(str, res))} = {sum(res)}')
        except TypeError:
            await bot.send_text(room, 'Missing argument')
        except ValueError:
            await bot.send_text(room, 'Invalid dice spec: {arg}')

    def help(self):
        return 'Roll dice'
