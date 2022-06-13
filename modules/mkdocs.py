from modules.common.module import BotModule
import requests
import re

class MatrixModule(BotModule):
    def __init__(self, name):
        super().__init__(name)
        self.rooms = dict()
        self.sites = dict()
        self.site_data = dict()

    def set_settings(self, data):
        super().set_settings(data)
        if data.get('rooms'):
            self.rooms = data['rooms']
        if data.get('sites'):
            self.shows = data['sites']

    def get_settings(self):
        data = super().get_settings()
        data['rooms'] = self.rooms
        data['sites'] = self.sites
        return data


    def matrix_start(self, bot):
        super().matrix_start(bot)
        self.bot = bot
        self.add_module_aliases(bot, ['search','find'])

    async def matrix_message(self, bot, room, event):
        args = event.body.split()
        cmd = args.pop(0).lower()
        if cmd == f'!{self.name}' and len(args):
            cmd = args.pop(0).lower()
        if cmd[0] == '!':
            cmd = cmd[1:]
        if cmd in ['setup']:
            bot.must_be_admin(room, event)
            self.logger.info(f"Setting up search for room {room.name}")
            self.rooms[room.room_id] = {
                'sites': {}
            }
            bot.save_settings()
            sites = self.rooms[room.room_id]
            return
        sites = self.rooms[room.room_id]

        if cmd in ['help']:
            return await bot.send_text(room, event, self.long_help(bot=bot, room=room, event=event))

        elif cmd in ['sites']:
            msg = ['Configured sites:']
            for name, config in sites.items():
                msg.append(f'- [{name}]({config["url"]}): Aliases [{",".join(config["aliases"])}')
            return await bot.send_text(room, event, "\n".join(msg))
        elif cmd in ['add']:
            bot.must_be_admin(room, event)
            self.logger.info(f'Adding site for room {room.name}')
            return await self.add_site(bot=bot, room=room, event=event, args=args)
        elif cmd in ['reindex']:
            bot.must_be_admin(room, event)
            return await self.populate_index(args[0], room=room)

        elif cmd in ['alias']:
            bot.must_be_admin(room, event)
            name, alias = args
            self.logger.info(f'Adding alias `{alias}` for site `{name}`')
            site = sites[name]
            site['aliases'].append(alias)

        elif cmd in ['search', 'find']:
            name_or_alias = args.pop(0).lower()
            site = self.get_site(name_or_alias, room=room)
            if not site:
                return await bot.send_text(room, event, f'Sorry, could not find settings for site or alias `{name_or_alias}`')
            results = await self.search_index(site, args)
            if len(results):
                msg = ['I found these results:']
                for (_, result) in results[:3]:
                    msg.append(f'- [{result.title}]({site["url"]}/{result.location}')
                # msg.append('For more results, see: ')
                return await bot.send_text(room, event, '\n'.join(msg))
            else:
                return await bot.send_text(room, event, 'Unable to find a reference for the search.')

    async def add_site(self, bot, room, event=None, args=[]):
        name, url = args
        sites = self.rooms[room.room_id]
        if sites.get(name):
            self.rooms[room.room_id][name]['url'] = url
            await bot.send_text(room, event, f'Updated url for site `{name}` for searching')
        else:
            self.rooms[room.room_id][name] = {
                'url': url,
                'aliases': []
            }
            await bot.send_text(room, event, f'Added new site `{name}` for searching')
        await self.populate_index(name, room=room)
        bot.save_settings()

    def get_site(self, name_or_alias, room):
        sites = self.rooms[room.room_id]
        if sites.get(name_or_alias):
            return sites[name_or_alias]
        else:
            for site in sites:
                if name_or_alias in site['alises']:
                    return site
        return None



    async def search_index(self, site, keywords):
        matches = []
        docs = self.site_data[site.url]
        for doc in reversed(docs):
            weight = 0
            for keyword in keywords:
                if re.search(keyword, doc['text'], re.IGNORECASE):
                    weight = weight + 1
            if weight > 0:
                matches.append((weight, doc))
        if len(keywords) > 1:
            matches.sort(key=lambda tup: tup[0])
        return matches

    async def populate_index(self, name, room):
        url = self.rooms[room.room_id][name]['url']
        response = requests.get(f'{url}/search/search_index.json').json()
        self.sites[name] = {
            'config': response['config'],
        }
        self.site_data[url] = []
        for doc in response['docs']:
            parts = doc.location.split('/')
            if len(parts) < 2:
                continue
            *_, tail = parts
            if tail.startswith("#"):
                # MKDocs search has index for different headers. Ignore.
                continue

            self.sites[url].append(doc)



    def help(self):
        return 'Search MkDocs sites for relevent pages'

    def long_help(self, bot=None, room=None, event=None):
        text = [
            self.help(),
            '- !search help: Show\'s this help text',
            '- !search sites: Shows configured sites',
            '- !search jbnotes Crystal: Searches site `jbnotes` for mentions of the Crystal programming language',
            '- !find notes NixOS Challenge: Searches alias notes for the words NixOS Challenge'
        ]
        if bot and room and event and bot.is_admin(room, event):
            text += [
                'Admin commands:',
                '- !search add jbnotes https://notes.jupiterbroadcasting.com: Adds the site `jbnotes`',
                '- !search alias jbnotes notes: Aliases the jbnotes site as notes',
                '- !search reindex jbnotes: Pulls the latest index'
            ]
        return '\n'.join(text)
