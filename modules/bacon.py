import random
from html import escape
from urllib.parse import quote

from modules.common.module import BotModule

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.bacons = [
            (
                0.96,
                'gives {} TWO strips of bacon 🥓🥓',
                'gives {} <strong>two</strong> strips of bacon 🥓🥓'
            ),
            (
                0.94,
                'gives {} a strip of immaculately cooked bacon 🥓',
                'gives {} a strip of <em>immaculately cooked</em> bacon 🥓'
            ),
            (
                0.84,
                'gives {} a strip of succulent bacon 🥓',
                'gives {} a strip of <em>succulent</em> bacon 🥓'
            ),
            (
                -0,92,
                'gives {} a strip of delicious bacon 🥓',
                'gives {} a strip of <em>delicious</em> bacon 🥓'
            ),
            (
                -0.96,
                'gives {} a strip of crispy bacon 🥓',
                'gives {} a strip of <em>crispy</em> bacon 🥓'
            ),
            (
                -0.98,
                'gives {} one egg, over-easy 🍳',
                'gives {} one egg, over-easy 🍳'
            ),
            (
                -0.99,
                "burned {}'s bacon, sorry.",
                "burned {}'s bacon, sorry."
            ),
            (
                -1.00,
                "EmptySkilletException: Bacon not found",
                "<strong>EmptySkilletException: Bacon not found</strong>"
            ),
        ]

    async def matrix_message(self, bot, room, event):
        self.logger.debug(f"room: {room.name} sender: {event.sender} asked for bacon")
        try:
            roll = event.source['content']['roll']
            if not bot.is_owner(event):
                return await bot.send_text(room, "{event.sender} isn't allowed in the kitchen")
            roll = float(roll) % 1.0
        except (AttributeError, KeyError, ValueError) as e:
            roll = random.uniform(-1,1)

        for n, plain, html in self.bacons:
            if roll >= n:
                break

        body = None
        try:
            _, body = event.body.split(None, 1)
            target = body
        except ValueError:
            target = event.sender
        plain = plain.format(target)

        try:
            _, target = event.formatted_body.split(None, 1)
        except (ValueError, AttributeError):
            if body:
                # no html: escape body
                target = escape(body)
            else:
                # no html, no target: use event.sender
                quoted = quote(event.sender, safe='/@:')
                target = f'<a href="https://matrix.to/#/{quoted}">{escape(event.sender)}</a>'

        await bot.send_html(room, html.format(target), plain, msgtype="m.emote")

    def help(self):
        return 'Ask for a strip of bacon'
