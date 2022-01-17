from modules.common.module import BotModule
from random import randrange

class MatrixModule(BotModule):

    async def matrix_message(self, bot, room, event):
        self.logger.info(f"room: {room.name}; sender: {event.sender} is rolling dice")
        args = event.body.split()[1:]
        if not args:
            return await bot.send_text(room, 'Missing dice argument')
        res = []
        bonus = 0
        try:
            for arg in args:
                if arg[0] in ['+', '-']:
                    bonus += int(arg)
                    continue
                count, sides = arg.split('d')
                sides = int(sides)
                count = int(count or 1)
                res += [1 + randrange(sides) for _ in range(count)]
        except ValueError:
            return await bot.send_text(room, f'Invalid dice spec: {arg}. Use the form [count]d[sides]')

        # only one die
        if len(res) < 2 and not bonus:
            return await bot.send_text(room, str(res[0]))

        rhs = sum(res) + bonus
        lhs = '+'.join(map(str, res))
        if bonus > 0:
            lhs += f'+{bonus}'
        elif bonus < 0:
            lhs += f'{bonus}'
        return await bot.send_text(room, f'{lhs} = {rhs}')

    def help(self):
        return 'Roll [count]d[sides] ... dice (e.g.: !roll 3d6 d20)'
