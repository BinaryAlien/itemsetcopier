from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import collections
import json
import re
import requests

CLIENT_VERSION = '10.9.1' # League of Legends client's current version (might not be up-to-date)

SET_NAME_MAX_LENGTH = 75

CODE_OK = 0x00
CODE_ERROR_SET_NAME_MAX_LENGTH = 0x01
CODE_ERROR_URL = 0x02
CODE_ERROR_CHAMPION = 0x03
CODE_ERROR_SERVER = 0x04
CODE_ERROR_OTHER = 0x05

items_data = requests.get('http://ddragon.leagueoflegends.com/cdn/' + CLIENT_VERSION + '/data/en_US/item.json').json()
champions_data = requests.get('http://ddragon.leagueoflegends.com/cdn/' + CLIENT_VERSION + '/data/en_US/champion.json').json()

def get_champion_id(champion_name):
	"""
		Matches a champion's name to it's corresponding ID
		Compares the champion's name to it's corresponding database name and ID (case insensitive)
		Returns 0 if no corresponding champion was found
	"""

	if not champion_name:
		return 0

	champion_name = champion_name.strip().lower()

	for champion in champions_data['data'].values():
		if champion_name == champion['id'].lower() or champion_name == champion['name'].lower():
			return int(champion['key'])

	return 0

class Translator(ABC):
	@abstractmethod
	def generate_item_set(self, set_name, url):
		pass

class MobafireTranslator(Translator):
	REGEX = r'((http|https):\/\/)?(www\.)?mobafire\.com\/league-of-legends\/build\/[A-Za-z0-9-]+-[0-9]{6}'

	def __init__(self):
		self._mobafire_items_map = {} # Matches a Mobafire item's name to it's corresponding ID

		for id_, item_data in items_data['data'].items():
			# Mobafire's trinkets doesn't have ' (Trinket)' in their name so we remove it
			# e.g.: 'Warding Totem (Trinket)' [LoL] -> 'Warding Totem' [Mobafire]
			name = item_data['name'].replace(' (Trinket)', '')

			self._mobafire_items_map[name] = id_

	def generate_item_set(self, set_name, url, build_index=0):
		if len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}

		if not re.match(MobafireTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid MOBAfire guide URL"}

		resp = requests.get(url)

		if resp.status_code != 200:
			return {'code': CODE_ERROR_SERVER, 'error': "Could not reach the given MOBAfire guide's webpage. Server returned status code {}".format(resp.status_code)}

		soup = BeautifulSoup(resp.text, 'html.parser')

		champion_name = soup.find('div', class_='title').find('h3').text
		champion_id = get_champion_id(champion_name)

		if champion_id == 0:
			raise TranslateException("Champion not found in database: '{}'".format(champion_name))

		builds = soup.find_all('div', class_='view-guide__build')

		if build_index >= len(builds):
			build_index = 0

		blocks = []
		outdated_items = set()

		for block_div in builds[build_index].find('div', class_='view-guide__build__items').find('div', class_='collapseBox').find_all('div', class_='view-guide__items'):
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
							Here we do some more alchemy because in the League of Legends' items database, enchanted jungle items have their own IDs but are named
							the same.

							For example, whether it is Skirmisher's Sabre or Stalker's Blade with 'Warrior' enchantment, both of them are named 'Enchantment: Warrior'.

							The only way of getting the right enchanted jungle item is to check from which items the enchanted jungle item was made, that's what
							we do here with 'from' which is a dict containing information about the items from which it was obtained.
						"""

						# The jungle item's name (without enchantment)
						jgl_item_name = jgl_item_name.group()

						# The jungle item's ID (without enchantment)
						jgl_item_id = self._mobafire_items_map[jgl_item_name]

						# The jungle item's name (with corresponding enchantment)
						jgl_enchantment = 'Enchantment: ' + jgl_enchantment.group()

						for id_, item_data in items_data['data'].items():
							if item_data['name'] != jgl_enchantment:
								continue

							if item_data.get('from'):
								# If the enchanted jungle item was made up the jungle item
								if jgl_item_id in item_data['from']:
									block['items'].append({'id': id_, 'count': count})
									break
				else:
					try:
						block['items'].append({'id': self._mobafire_items_map[item_name], 'count': count})
					except KeyError as ex:
						outdated_items.add(ex.args[0])
						continue

			blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_id],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {
			'code': CODE_OK,
			'item_set': item_set,
			'outdated_items': outdated_items,
		}

class MobalyticsTranslator(Translator):
	REGEX = r'((http|https):\/\/)?app\.mobalytics\.gg\/champions\/[A-Za-z]+\/build'

	def generate_item_set(self, set_name, url, build_name=None):
		if len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}

		if not re.match(MobalyticsTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid Mobalytics build URL"}

		champion_name = url.split('/')[-2]
		champion_id = get_champion_id(champion_name)

		if champion_id == 0:
			return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found in database: '{}'".format(champion_name)}

		resp = requests.get('https://api.mobalytics.gg/lol/champions/v1/meta', params={'name': champion_name.lower()})

		if resp.status_code != 200:
			return {'code': CODE_ERROR_SERVER, 'error': "Could not reach the given Mobalytics build's data. Server returned status code {}".format(resp.status_code)}

		data = resp.json()

		build_to_translate = None

		if build_name:
			build_name = build_name.strip().lower()

			for role in data['data']['roles']:
				for build in role['builds']:
					if build['name'].strip().lower() == build_name:
						build_to_translate = build
						break
		else:
			# By default we pick the first build of the first role
			build_to_translate = data['data']['roles'][0]['builds'][0]

		if not build_to_translate:
			return {'code': CODE_ERROR_OTHER, 'error': "Could not retrieve the build's data"}

		blocks = []

		for block_id, items in build_to_translate['items']['general'].items():
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

		for situational in build_to_translate['items']['situational']:
			block = {}
			block['type'] = "Situational - " + situational['name']
			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""

			counter = collections.Counter(situational['build'])
			block['items'] = []

			for id_, count in dict(counter).items():
				block['items'].append({'id': id_, 'count': count})

			blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_id],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}

class OpggTranslator(Translator):
	REGEX = r'((http|https):\/\/)?((www|na)?\.)?op\.gg\/champion\/[A-Za-z]+\/statistics\/(top|jungle|mid|bot|support)'

	def generate_item_set(self, set_name, url):
		if len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}

		if not re.match(OpggTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid OP.GG build URL"}

		champion_name = url.split('/')[-3]
		champion_id = get_champion_id(champion_name)

		if champion_id == 0:
			return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found in database: '{}'".format(champion_name)}

		resp = requests.get(url)

		if resp.status_code != 200:
			return {'code': CODE_ERROR_SERVER, 'error': "Could not reach the given OP.GG build's webpage. Server returned status code {}".format(resp.status_code)}

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
			'associatedChampions': [champion_id],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}

class ChampionggTranslator(Translator):
	REGEX = r'((http|https):\/\/)?(www\.)?champion\.gg\/champion\/[A-Za-z]+\/(Top|Jungle|Middle|ADC|Support)'

	def generate_item_set(self, set_name, url):
		if len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_ERROR_SET_NAME_MAX_LENGTH, 'error': "The maximum length of an item set's name is 75 characters"}

		if not re.match(ChampionggTranslator.REGEX, url):
			return {'code': CODE_ERROR_URL, 'error': "Invalid OP.GG build URL"}

		champion_name = url.split('/')[-2]
		champion_id = get_champion_id(champion_name)

		if champion_id == 0:
			return {'code': CODE_ERROR_CHAMPION, 'error': "Champion not found in database: '{}'".format(champion_name)}

		resp = requests.get(url)

		if resp.status_code != 200:
			return {'code': CODE_ERROR_SERVER, 'error': "Could not reach the given Champion.gg build's webpage. Server returned status code {}".format(resp.status_code)}

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
			'associatedChampions': [champion_id],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}
