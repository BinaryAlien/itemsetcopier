from bs4 import BeautifulSoup
from enum import IntEnum
from urllib.parse import urlparse
from time import time
import aiohttp
import asyncio
import collections
import json
import re


SET_NAME_MAX_LENGTH = 75

REGEX_MOBAFIRE   = r'^((http|https):\/\/)?(www\.)?mobafire\.com\/league-of-legends\/build\/[A-Za-z0-9-]+-[0-9]{6}$'
ROLES_MOBALYTICS = ('top', 'jungle', 'mid', 'adc', 'support')
ROLES_OPGG       = ('top', 'jungle', 'mid', 'bot', 'support')

REQUEST_TIMEOUT    = 10    # in seconds
DATA_REFRESH_DELAY = 86400 # in seconds


class Translator(IntEnum):
	MOBAFIRE =   0
	MOBALYTICS = 1
	OPGG =       2
	CHAMPIONGG = 3


class ReturnCode(IntEnum):
	CODE_OK               = 0x00
	ERR_INVALID_PARAM     = 0x01 # Invalid parameter type/Non-optional parameter was not specified
	ERR_SET_NAME_LENGTH   = 0x02 # Set name length is invalid
	ERR_REMOTE_FAIL       = 0x03 # Error while fetching resource from remote server
	ERR_INVALID_CHAMP     = 0x04 # Invalid champion
	ERR_OTHER             = 0xFF # Specific errors


cache = {
	'version': None,   # Latest version of the game
	'items': None,     # Latest items data
	'champions': None, # Latest champion data
	'time': -1         # UNIX timestamp of the last refresh
}


async def fetch_game_data():
	if time() - cache['time'] >= DATA_REFRESH_DELAY or not cache['version']:
		async with aiohttp.ClientSession() as sess:
			try:
				async with sess.get('https://ddragon.leagueoflegends.com/api/versions.json', timeout=REQUEST_TIMEOUT) as resp:
					if resp.status != 200:
						raise RuntimeError("Could not retrieve latest game version number from League of Legends CDN")

					try:
						versions = await resp.json()
					except json.JSONDecodeError:
						raise RuntimeError("Could not retrieve latest game version number from League of Legends CDN")

					version = versions[0]

					items = await fetch_items(version)
					champions = await fetch_champions(version)

					cache['version'] = version
					cache['items'] = items
					cache['champions'] = champions
					cache['time'] = round(time())
			except asyncio.TimeoutError:
				raise RuntimeError("Could not retrieve latest game version number from League of Legends CDN")

	return {'items': cache['items'], 'champions': cache['champions']}


async def fetch_items(version):
	async with aiohttp.ClientSession() as sess:
		try:
			async with sess.get('https://ddragon.leagueoflegends.com/cdn/' + version + '/data/en_US/item.json', timeout=REQUEST_TIMEOUT) as resp:
				if resp.status != 200:
					raise RuntimeError("Could not retrieve items data from League of Legends CDN")

				try:
					return await resp.json()
				except json.JSONDecodeError:
					raise RuntimeError("Could not retrieve items data from League of Legends CDN")
		except asyncio.TimeoutError:
			pass

	raise RuntimeError("Could not retrieve items data from League of Legends CDN")


async def fetch_champions(version):
	async with aiohttp.ClientSession() as sess:
		try:
			async with sess.get('https://ddragon.leagueoflegends.com/cdn/' + version + '/data/en_US/champion.json', timeout=REQUEST_TIMEOUT) as resp:
				if resp.status != 200:
					raise RuntimeError("Could not retrieve champions data from League of Legends CDN")

				try:
					return await resp.json()
				except json.JSONDecodeError:
					raise RuntimeError("Could not retrieve champions data from League of Legends CDN")
		except asyncio.TimeoutError:
			pass

	raise RuntimeError("Could not retrieve items data from League of Legends CDN")


async def get_champion_by_name(champion_name):
	if not champion_name or not isinstance(champion_name, str):
		raise ValueError("champion_name must be a str")

	champion_name = champion_name.strip().lower()
	game_data = await fetch_game_data()

	for champion in game_data['champions']['data'].values():
		if champion_name == champion['id'].lower() or champion_name == champion['name'].lower():
			return champion

	raise LookupError("Could not find champion '" + champion_name + "'")


async def get_champion_by_key(champion_key):
	if not champion_key or not isinstance(champion_key, int):
		raise ValueError("champion_key must be an int")

	champion_key = str(champion_key)
	game_data = await fetch_game_data()

	for champion in game_data['champions']['data'].values():
		if champion_key == champion['key']:
			return champion

	raise LookupError("Could not find champion with key " + str(champion_key))


async def translate(identifier, **params):
	if identifier == Translator.MOBAFIRE:
		return await translate_mobafire(**params)

	if identifier == Translator.MOBALYTICS:
		return await translate_mobalytics(**params)

	if identifier == Translator.OPGG:
		return await translate_opgg(**params)

	if identifier == Translator.CHAMPIONGG:
		return await translate_championgg(**params)

	raise RuntimeError("Unknown translator")


async def translate_mobafire(set_name=None, url=None, build_index=0):
	if set_name is None:
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specify 'set_name'"}

	if not isinstance(set_name, str):
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "set_name must be an str"}

	if len(set_name) < 1 or len(set_name) > SET_NAME_MAX_LENGTH:
		return {'code': ReturnCode.ERR_SET_NAME_LENGTH, 'error': "The length of an item set's name must be between 1 and {} characters included".format(SET_NAME_MAX_LENGTH)}

	if url is None:
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specify 'url'"}

	if not isinstance(url, str):
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "url must be an str"}

	if not re.match(REGEX_MOBAFIRE, url):
		return {'code': ReturnCode.ERR_OTHER, 'error': "Invalid MOBAfire guide URL"}

	if build_index is None:
		build_index = 0
	elif not isinstance(build_index, int):
		try:
			build_index = int(build_index)
		except ValueError:
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "build_index must be an int"}

	url = urlparse(url, 'https')

	async with aiohttp.ClientSession() as sess:
		try:
			async with sess.get(url.scheme + '://' + url.netloc + url.path, timeout=REQUEST_TIMEOUT) as resp:
				if resp.status != 200:
					return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Unexpected response from the given MOBAfire guide's webpage. Server returned status code " + str(resp.status)}

				html = await resp.text()
				soup = BeautifulSoup(html, 'html.parser')

				# TODO
				title = soup.find('title').text.split(' ')
				champion_name = ''

				for word in title:
					if word == 'Build':
						break

					champion_name += ' ' + word

				try:
					champion = await get_champion_by_name(champion_name)
				except LookupError:
					return {'code': ReturnCode.ERR_INVALID_CHAMP, 'error': "Champion not found: '" + champion_name + "'"}
				except RuntimeError:
					return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not retrieve champions data from the League of Legends CDN"}

				builds = soup.find_all('div', class_='view-guide__build')

				if build_index < 0 or build_index >= len(builds):
					build_index = 0

				blocks_html = builds[build_index] \
					.find('div', class_='view-guide__build__items') \
					.find('div', class_='collapseBox') \
					.find_all('div', class_='view-guide__items')

				blocks = []            # item set's blocks
				outdated_items = set() # set of strings containing the build's outdated items

				try:
					game_data = await fetch_game_data()
				except RuntimeError:
					return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not retrive items data from the League of Legends CDN"}

				for block_html in blocks_html:
					block = {
							'showIfSummonerSpell': "",
							'hideIfSummonerSpell': "",
							'items': []
						}

					block_title = block_html.find('div', class_='view-guide__items__bar').span.text
					block['type'] = block_title

					block_items_html = block_html \
						.find('div', class_='view-guide__items__content') \
						.find_all('span', class_=re.compile(r'ajax-tooltip {t:\'Item\',i:\'[0-9]+\'}'))

					for item in block_items_html:
						item_name = item.a.span.text # name of the item on Mobafire
						count_tag = item.a.find('label')

						if count_tag:
							count = int(count_tag.text)
						else:
							count = 1

						jgl_item_name = re.search(r'(Stalker\'s Blade|Skirmisher\'s Sabre)', item_name)

						if jgl_item_name:
							jgl_enchantment = re.search(r'(Warrior|Cinderhulk|Runic Echoes|Bloodrazor)', item_name)

							if jgl_enchantment:
								"""
									Here we do some more processing due to the League of Legends' items data design:
									enchanted jungle items have their own IDs but are named the same.

									For example, whether it is "Skirmisher's Sabre" or "Stalker's Blade"
									with "Warrior" enchantment, both of them are named 'Enchantment: Warrior'.

									The only way of getting the right enchanted jungle item is to check
									from which items the enchanted jungle item was made, that's what
									we do here with "from" which is a dict containing information about
									the items from which it was obtained.
								"""

								# the jungle item's name (without enchantment)
								jgl_item_name = jgl_item_name.group()

								# the jungle item's ID (without enchantment)
								jgl_item_id = None

								# the jungle item's ID (without enchantment)
								for id_, item in game_data['items']['data'].items():
									if item['name'] == jgl_item_name:
										jgl_item_id = id_
										break

								if not jgl_item_id:
									outdated_items.add(item_name)
									continue

								# the jungle item's name (with corresponding enchantment)
								jgl_enchantment = 'Enchantment: ' + jgl_enchantment.group()

								for id_, item in game_data['items']['data'].items():
									if item['name'] != jgl_enchantment:
										continue

									if item.get('from'):
										# if the enchanted jungle item was made with the matching jungle item
										if jgl_item_id in item['from']:
											block['items'].append({'id': id_, 'count': count})
											break
						else:
							item_id = None

							for id_, item in game_data['items']['data'].items():
								if item['name'].replace(" (Trinket)", "") == item_name:
									item_id = id_
									break

							if item_id:
								block['items'].append({'id': item_id, 'count': count})
							else:
								outdated_items.add(item_name)

					blocks.append(block)

				item_set = json.dumps({
					'associatedChampions': [int(champion['key'])],
					'associatedMaps': [],
					'title': set_name,
					'blocks': blocks,
				})

				return {
					'code': ReturnCode.CODE_OK,
					'item_set': item_set,
					'outdated_items': list(outdated_items),
				}
		except asyncio.TimeoutError:
			return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not reach MOBAfire guide's webpage"}


async def translate_mobalytics(champion_key=None, champion_name=None, role=None):
	if role is None:
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specifiy 'role': " + "/".join(ROLES_MOBALYTICS)}
	
	if not isinstance(role, str):
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "role must be " + "/".join(ROLES_MOBALYTICS)}
	
	role = role.lower()

	if not role in ROLES_MOBALYTICS:
		return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "role must be " + "/".join(ROLES_MOBALYTICS)}
	
	if champion_key is None:
		if champion_name is None:
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specifiy at least 'champion_key' or 'champion_name'"}

		if not isinstance(champion_name, str):
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "champion_name must be an str"}

		try:
			champion = await get_champion_by_name(champion_name)
			champion_key = int(champion['key'])
		except LookupError:
			return {'code': ReturnCode.ERR_INVALID_CHAMP, 'error': "Champion not found " + champion_name}
		except RuntimeError:
			return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not retrieve champions data from the League of Legends CDN"}
	else:
		if not isinstance(champion_key, int):
			try:
				champion_key = int(champion_key)
			except ValueError:
				return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "champion_key must be an int"}

		try:
			champion = await get_champion_by_key(champion_key)
			champion_name = champion['name']
		except LookupError:
			return {'code': ReturnCode.ERR_INVALID_CHAMP, 'error': "Champion with key " + str(champion_key) + " not found"}
		except RuntimeError:
			return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not retrieve champions data from the League of Legends CDN"}
	
	async with aiohttp.ClientSession() as sess:
		try:
			async with sess.get('https://api.mobalytics.gg/lol/champions/v1/meta', params={'name': champion_name}, timeout=REQUEST_TIMEOUT) as resp:
				# Mime type of response is 'text/plain' so we cannot use `resp.json` (or an error is thrown)
				text = await resp.text()
				data = json.loads(text)

				if resp.status != 200:
					if resp.status == 404:
						return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not reach the given Mobalytics build's data. Server returned status code 404 (there may be no Mobalytics builds for this champion yet)"}

					return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not reach the given Mobalytics build's data. Server returned status code " + str(resp.status_code)}

				item_sets = []

				for role_data in data['data']['roles']:
					if role_data['name'] == role:
						for build in role_data['builds']:
							blocks = []

							for block_id, items in build['items']['general'].items():
								block = {
									'showIfSummonerSpell': "",
									'hideIfSummonerSpell': "",
									'items': []
								}

								if block_id == 'start':
									block['type'] = "Starter"
								elif block_id == 'early':
									block['type'] = "Early items"
								elif block_id == 'core':
									block['type'] = "Core items"
								elif block_id == 'full':
									block['type'] = "Full build"
								else:
									block['type'] = "???"

								counter = collections.Counter(items)

								for id, count in dict(counter).items():
									block['items'].append({'id': id, 'count': count})

								if block_id == 'start':
									blocks.insert(0, block)
								else:
									blocks.append(block)

							for situational in build['items']['situational']:
								block_title = "Situational - " + situational['name']

								block = {
									'showIfSummonerSpell': "",
									'hideIfSummonerSpell': "",
									'items': [],
									'type': block_title
								}

								counter = collections.Counter(situational['build'])

								for id, count in dict(counter).items():
									block['items'].append({'id': id, 'count': count})

								blocks.append(block)

							item_set = {
								'associatedChampions': [champion_key],
								'associatedMaps': [],
								'title': build['name'],
								'blocks': blocks,
							}

							item_sets.append(item_set)

						return {'code': ReturnCode.CODE_OK, 'item_set': json.dumps(item_sets)}

			return {'code': ReturnCode.ERR_OTHER, 'error': "Champion '{}' does not have builds for role {}".format(champion_name, role)}
		except asyncio.TimeoutError:
			return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not reach the Mobalytics build's data"}


async def translate_opgg(set_name=None, champion_key=None, champion_name=None, role=None):
		if set_name is None:
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specify 'set_name'"}

		if not isinstance(set_name, str):
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "set_name must be an str"}

		if len(set_name) < 1 or len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': ReturnCode.ERR_SET_NAME_LENGTH, 'error': "The length of an item set's name must be between 1 and {} characters included".format(SET_NAME_MAX_LENGTH)}

		if role is None:
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specify 'role': " + "/".join(ROLES_OPGG)}

		if not isinstance(role, str):
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "role must be an str"}

		role = role.lower()

		if not role in ROLES_OPGG:
			return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "role must be " + "/".join(ROLES_OPGG)}

		if champion_key is None:
			if champion_name is None:
				return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "Must specifiy at least 'champion_key' or 'champion_name'"}

			if not isinstance(champion_name, str):
				return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "champion_name must be an str"}

			try:
				champion = await get_champion_by_name(champion_name)
				champion_key = int(champion['key'])
			except LookupError:
				return {'code': ReturnCode.ERR_INVALID_CHAMP, 'error': "Champion not found " + champion_name}
			except RuntimeError:
				return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not retrieve champions data from the League of Legends CDN"}
		else:
			if not isinstance(champion_key, int):
				try:
					champion_key = int(champion_key)
				except ValueError:
					return {'code': ReturnCode.ERR_INVALID_PARAM, 'error': "champion_key must be an int"}

			try:
				champion = await get_champion_by_key(champion_key)
				champion_name = champion['name']
			except LookupError:
				return {'code': ReturnCode.ERR_INVALID_CHAMP, 'error': "Champion with key " + str(champion_key) + " not found"}
			except RuntimeError:
				return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		url = "https://www.op.gg/champion/{}/statistics/{}".format(champion_name, role)

		async with aiohttp.ClientSession() as sess:
			try:
				async with sess.get(url, timeout=REQUEST_TIMEOUT) as resp:
					if resp.status != 200:
						return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not reach the given OP.GG build's webpage. Server returned status code " + str(resp.status)}

					if resp.history and resp.url != url:
						return {'code': ReturnCode.ERR_OTHER, 'error': "Champion '{}' does not have builds for role {}/does not have any builds yet".format(champion_name, role)}

					html = await resp.text()

					soup = BeautifulSoup(html, 'html.parser')
					rows = soup.find_all('table', class_='champion-overview__table')[1].tbody.find_all('tr')

					category_title = "???"
					blocks = []

					for row in rows:
						block = {
							'showIfSummonerSpell': "",
							'hideIfSummonerSpell': "",
							'items': []
						}

						# if this row is the first of a new category
						if 'champion-overview__row--first' in row['class']:
							# we retrieve the category name
							category_title = row.th.text

						pick_rate = row.find('td', class_='champion-overview__stats--pick').strong.text

						block['type'] = category_title + " (" + pick_rate + " pick rate)"

						for item_html in row.find('td', class_=['champion-overview__data', 'champion-overview__border', 'champion-overview__border--first']).ul.find_all('li', class_=['champion-stats__list__item', 'tip']):
							id_ = item_html.img['src'].split('/')[-1].split('.png')[0] # extract item's ID from image's URL
							block['items'].append({'id': id_, 'count': 1})

						blocks.append(block)

					item_set = json.dumps({
						'associatedChampions': [champion_key],
						'associatedMaps': [],
						'title': set_name,
						'blocks': blocks,
					})

					return {'code': ReturnCode.CODE_OK, 'item_set': item_set}
			except asyncio.TimeoutError:
				return {'code': ReturnCode.ERR_REMOTE_FAIL, 'error': "Could not reach the given OP.GG build's webpage"}

async def translate_championgg(set_name=None, champion_key=None, champion_name=None, role=None):
	raise NotImplementedError()
