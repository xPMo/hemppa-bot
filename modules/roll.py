from modules.common.module import BotModule
from random import randrange

class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        self.logger.info(f"room: {room.name} sender: {event.sender} is rolling dice")
        args = event.body.split()[1:]
        if not args:
            return await bot.send_text(room, 'Missing argument')
        try:
            res = []
            for arg in args:
                count, sides = arg.split('d')
                sides = int(sides)
                count = int(count or 1)
                res += [1 + randrange(sides) for _ in range(count)]
            if len(res) < 2:
                return await bot.send_text(room, str(res[0]))
            return await bot.send_text(room, f'{"+".join(map(str, res))} = {sum(res)}')
        except ValueError:
            return await bot.send_text(room, f'Invalid dice spec: {arg}. Use the form [count]d[sides]')

    def help(self):
        return 'Roll [count]d[sides] ... dice (e.g.: !roll 3d6 d20)'
