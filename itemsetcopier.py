from bs4 import BeautifulSoup
import collections
import json
import re
import requests

SET_NAME_MAX_LENGTH = 75

CODE_OK = 0x00
CODE_ERROR_SET_NAME_MAX_LENGTH = 0x01
CODE_ERROR_URL = 0x02
CODE_ERROR_CHAMPION = 0x03
CODE_ERROR_REMOTE = 0x04
CODE_ERROR_CDN = 0x05
CODE_ERROR_INVALID_INPUT = 0x06

CLIENT_VERSION = '10.13.1' # League of Legends client's current version (might not be up-to-date)
REQUEST_TIMEOUT = 10

cache = {'item': None, 'champion': None}

def items():
	if not cache['item']:
		try:
			resp = requests.get('https://ddragon.leagueoflegends.com/cdn/' + CLIENT_VERSION + '/data/en_US/item.json', timeout=REQUEST_TIMEOUT)
		except requests.exceptions.RequestException:
			raise RuntimeError("could not retrieve items data from League of Legends CDN")

		if not resp.status_code == 200:
			raise RuntimeError("could not retrieve items data from League of Legends CDN")

		try:
			cache['item'] = resp.json()
		except json.JSONDecodeError:
			raise RuntimeError("could not retrieve items data from League of Legends CDN")

	return cache['item']

def champions():
	if not cache['champion']:
		try:
			resp = requests.get('https://ddragon.leagueoflegends.com/cdn/' + CLIENT_VERSION + '/data/en_US/champion.json', timeout=REQUEST_TIMEOUT)
		except requests.exceptions.RequestException:
			raise RuntimeError("could not retrieve champions data from League of Legends CDN")

		if not resp.status_code == 200:
			raise RuntimeError("could not retrieve champions data from League of Legends CDN")

		try:
			cache['champion'] = resp.json()
		except json.JSONDecodeError:
			raise RuntimeError("could not retrieve champions data from League of Legends CDN")

	return cache['champion']

def get_champion_key(champion_name):
	"""
		Matches a champion name to it's corresponding ID
		Raises LookupError if the champion was not found
	"""

	if not champion_name:
		raise LookupError

	champion_name = champion_name.strip().lower()

	for champion in champions()['data'].values():
		if champion_name == champion['id'].lower() or champion_name == champion['name'].lower():
			return int(champion['key'])

	raise LookupError

class Translator:
	@staticmethod
	def generate_item_set(*args, **kwargs):
		pass

class MobafireTranslator(Translator):
	REGEX = r'^((http|https):\/\/)?(www\.)?mobafire\.com\/league-of-legends\/build\/[A-Za-z0-9-]+-[0-9]{6}$'

	@staticmethod
	def _get_item_id(mobafire_name):
		for id, item in items()['data'].items():
			# Mobafire's trinkets doesn't have ' (Trinket)' in their name so we remove it
			# e.g.: 'Warding Totem (Trinket)' [LoL] -> 'Warding Totem' [Mobafire]

			if mobafire_name == item['name'].replace(" (Trinket)", ""):
				return id

		raise LookupError

	@staticmethod
	def generate_item_set(set_name=None, url=None, build_index=1, *args, **kwargs):
		if set_name is None:
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify 'set_name'"}
		elif not isinstance(set_name, str):
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "set_name must be an str"}
		elif url is None:
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify 'url'"}
		elif not isinstance(url, str):
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "url must be an str"}
		elif build_index is None:
			build_index = 1
		elif not isinstance(build_index, int):
			try:
				build_index = int(build_index)
			except ValueError:
				return {'code': CODE_ERROR_INVALID_INPUT, 'error': "build_index must be an int"}
		elif len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}
		elif not re.match(MobafireTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid MOBAfire guide URL"}

		resp = requests.get(url)

		if resp.status_code != 200:
			return {'code': CODE_ERROR_REMOTE, 'error': "Could not reach the given MOBAfire guide's webpage. Server returned status code {}".format(resp.status_code)}

		soup = BeautifulSoup(resp.text, 'html.parser')

		champion_name = soup.find('div', class_='title').find('h3').text

		try:
			champion_key = get_champion_key(champion_name)
		except LookupError:
			return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
		except RuntimeError:
			return {'code': CODE_ERROR_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		builds = soup.find_all('div', class_='view-guide__build')

		if build_index < 1 or build_index > len(builds):
			build_index = 1

		blocks = []
		outdated_items = set()

		for block_div in builds[build_index - 1].find('div', class_='view-guide__build__items').find('div', class_='collapseBox').find_all('div', class_='view-guide__items'):
			block = {}
			block['type'] = block_div.find('div', class_='view-guide__items__bar').span.text # Name of the block
			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""
			block['items'] = []

			for item in block_div.find('div', class_='view-guide__items__content').find_all('span', class_=re.compile(r'ajax-tooltip {t:\'Item\',i:\'[0-9]+\'}')):
				item_name = item.a.span.text # Name of the item on Mobafire
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
							Here we do some more alchemy because in the League of Legends' items data, enchanted jungle items have their own IDs but are named the same.

							For example, whether it is Skirmisher's Sabre or Stalker's Blade with 'Warrior' enchantment, both of them are named 'Enchantment: Warrior'.

							The only way of getting the right enchanted jungle item is to check from which items the enchanted jungle item was made, that's what
							we do here with 'from' which is a dict containing information about the items from which it was obtained.
						"""

						# The jungle item's name (without enchantment)
						jgl_item_name = jgl_item_name.group()

						try:
							# The jungle item's ID (without enchantment)
							jgl_item_id = MobafireTranslator._get_item_id(jgl_item_name)
						except LookupError:
							outdated_items.add(item_name)
							continue
						except RuntimeError:
							return {'code': CODE_ERROR_CDN, 'error': "Could not retrive items data from League of Legends CDN"}

						# The jungle item's name (with corresponding enchantment)
						jgl_enchantment = 'Enchantment: ' + jgl_enchantment.group()

						for id_, item in items()['data'].items():
							if item['name'] != jgl_enchantment:
								continue

							if item.get('from'):
								# If the enchanted jungle item was made up the jungle item
								if jgl_item_id in item['from']:
									block['items'].append({'id': id_, 'count': count})
									break
				else:
					try:
						block['items'].append({'id': MobafireTranslator._get_item_id(item_name), 'count': count})
					except LookupError:
						outdated_items.add(item_name)
						continue
					except RuntimeError:
						return {'code': CODE_ERROR_CDN, 'error': "Could not retrive items data from League of Legends CDN"}

			blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_key],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {
			'code': CODE_OK,
			'item_set': item_set,
			'outdated_items': list(outdated_items),
		}

class MobalyticsTranslator(Translator):
	@staticmethod
	def generate_item_set(champion_key=None, champion_name=None, *args, **kwargs):
		if champion_key is None:
			if champion_name is None:
				return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify at least 'champion_key' or 'champion_name'"}
			elif not isinstance(champion_name, str):
				return {'code': CODE_ERROR_INVALID_INPUT, 'error': "champion_name must be an str"}
			else:
				try:
					champion_key = get_champion_key(champion_name)
				except LookupError:
					return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
				except RuntimeError:
					return {'code': CODE_ERROR_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}
		else:
			if not isinstance(champion_key, int):
				try:
					champion_key = int(champion_key)
				except ValueError:
					return {'code': CODE_ERROR_INVALID_INPUT, 'error': "champion_key must be an int"}

			valid = False
			champion_key_str = str(champion_key)

			try:
				for champion in champions()['data'].values():
					if champion['key'] == champion_key_str:
						valid = True
						champion_name = champion['id']
						break
			except RuntimeError:
				return {'code': CODE_ERROR_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

			if not valid:
				return {'code': CODE_ERROR_CHAMPION, 'error': "Champion with key '{}' not found".format(champion_key)}

		resp = requests.get('https://api.mobalytics.gg/lol/champions/v1/meta', params={'name': champion_name})

		if resp.status_code != 200:
			return {'code': CODE_ERROR_REMOTE, 'error': "Could not reach the given Mobalytics build's  Server returned status code {}".format(resp.status_code)}

		mobalytics_data = resp.json()
		item_sets = []

		for role in mobalytics_data['data']['roles']:
			for build in role['builds']:

				blocks = []

				for block_id, items in build['items']['general'].items():
					block = {}

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

					block['showIfSummonerSpell'] = ""
					block['hideIfSummonerSpell'] = ""

					counter = collections.Counter(items)
					block['items'] = []

					for id_, count in dict(counter).items():
						block['items'].append({'id': id_, 'count': count})

					if block_id == 'start':
						blocks.insert(0, block)
					else:
						blocks.append(block)

				for situational in build['items']['situational']:
					block = {}
					block['type'] = "Situational - " + situational['name']
					block['showIfSummonerSpell'] = ""
					block['hideIfSummonerSpell'] = ""

					counter = collections.Counter(situational['build'])
					block['items'] = []

					for id_, count in dict(counter).items():
						block['items'].append({'id': id_, 'count': count})

					blocks.append(block)

				item_set = {
					'associatedChampions': [champion_key],
					'associatedMaps': [],
					'title': build['name'],
					'blocks': blocks,
				}

				item_sets.append(item_set)

		return {'code': CODE_OK, 'item_set': json.dumps(item_sets)}

class OpggTranslator(Translator):
	REGEX = r'^((http|https):\/\/)?((www|na|euw)?\.)?op\.gg\/champion\/[A-Za-z]+\/statistics\/(top|jungle|mid|bot|support)$'

	@staticmethod
	def generate_item_set(set_name=None, url=None, *args, **kwargs):
		if set_name is None:
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify 'set_name'"}
		elif not isinstance(set_name, str):
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "set_name must be an str"}
		elif url is None:
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify 'url'"}
		elif not isinstance(url, str):
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "url must be an str"}
		elif len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}
		elif not re.match(OpggTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid OP.GG build URL"}

		champion_name = url.split('/')[-3]

		try:
			champion_key = get_champion_key(champion_name)
		except LookupError:
			return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
		except RuntimeError:
			return {'code': CODE_ERROR_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		resp = requests.get(url)

		if resp.status_code != 200:
			return {'code': CODE_ERROR_REMOTE, 'error': "Could not reach the given OP.GG build's webpage. Server returned status code {}".format(resp.status_code)}

		soup = BeautifulSoup(resp.text, 'html.parser')
		rows = soup.find_all('table', class_='champion-overview__table')[1].tbody.find_all('tr')

		category_title = "???"

		blocks = []

		for index, row in enumerate(rows):
			block = {}

			# If this row is the first of a new category
			if len(row['class']) == 2 and row['class'][1] == 'champion-overview__row--first':
				# We retrieve the category name
				category_title = row.th.text

			pick_rate = row.find('td', class_='champion-overview__stats--pick').strong.text

			block['type'] = "{} ({} pick rate)".format(category_title, pick_rate)
			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""
			block['items'] = []

			for item_li in row.find('td', class_=['champion-overview__data', 'champion-overview__border', 'champion-overview__border--first']).ul.find_all('li', class_=['champion-stats__list__item', 'tip']):
				id_ = item_li.img['src'].split('/')[-1].split('.png')[0] # Extract item's ID from image's URL
				block['items'].append({'id': id_, 'count': 1})

			blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_key],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}

class ChampionggTranslator(Translator):
	REGEX = r'^((http|https):\/\/)?(www\.)?champion\.gg\/champion\/[A-Za-z]+\/(Top|Jungle|Middle|ADC|Support)$'

	@staticmethod
	def generate_item_set(set_name=None, url=None, *args, **kwargs):
		if set_name is None:
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify 'set_name'"}
		elif not isinstance(set_name, str):
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "set_name must be an str"}
		elif url is None:
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "Must specify 'url'"}
		elif not isinstance(url, str):
			return {'code': CODE_ERROR_INVALID_INPUT, 'error': "url must be an str"}
		elif len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}
		elif not re.match(ChampionggTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid OP.GG build URL"}

		champion_name = url.split('/')[-2]

		try:
			champion_key = get_champion_key(champion_name)
		except LookupError:
			return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
		except RuntimeError:
			return {'code': CODE_ERROR_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		resp = requests.get(url)

		if resp.status_code != 200:
			return {'code': CODE_ERROR_REMOTE, 'error': "Could not reach the given Champion.GG build's webpage. Server returned status code {}".format(resp.status_code)}

		soup = BeautifulSoup(resp.text, 'html.parser')

		sections = soup.find_all('div', class_='champion-area')[1].find_all('div', class_='col-xs-12 col-sm-12 col-md-6')[1].find_all('div', class_=['col-xs-12', 'col-sm-12'])
		sections.reverse()

		blocks = []

		for section in sections:
			builds = section.find_all('div', class_='build-wrapper')
			names = section.find_all('h2', class_='champion-stats')

			for i in range(len(builds)):
				block = {}
				block['type'] = names[i].text
				block['showIfSummonerSpell'] = ""
				block['hideIfSummonerSpell'] = ""
				block['items'] = []

				for a in builds[i].find_all('a'):
					id_ = a.img['src'].split('/')[-1].split('.png')[0] # Extract item's ID from image's URL
					block['items'].append({'id': id_, 'count': 1})

				blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_key],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}
