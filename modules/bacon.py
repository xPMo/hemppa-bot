import random
from html import escape
from urllib.parse import quote

from modules.common.module import BotModule

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.bacons = [
            (
                0.99,
                'gives {} a strip of immaculately cooked bacon 🥓',
                'gives {} a strip of <em>immaculately cooked</em> bacon 🥓'
            ),
            (
                0.04,
                'gives {} a strip of delicious bacon 🥓',
                'gives {} a strip of <em>delicious</em> bacon 🥓'
            ),
            (
                0.02,
                'gives {} a strip of crispy bacon 🥓',
                'gives {} a strip of <em>crispy</em> bacon 🥓'
            ),
            (
                0.01,
                'gives {} one egg, over-easy 🍳',
                'gives {} one egg, over-easy 🍳'
            ),
            (
                0.005,
                "burned {}'s bacon, sorry.",
                "burned {}'s bacon, sorry."
            ),
            (
                0,
                "EmptySkilletException: Bacon not found",
                "<strong>EmptySkilletException: Bacon not found</strong>"
            )
        ]

    async def matrix_message(self, bot, room, event):
        self.logger.debug(f"room: {room.name} sender: {event.sender} asked for bacon")
        rand = random.uniform(0,1)
        for n, plain, html in self.bacons:
            if rand >= n:
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
