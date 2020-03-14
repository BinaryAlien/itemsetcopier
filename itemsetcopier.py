from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import collections
import json
import os
import re
import requests

CLIENT_VERSION = '10.5.1' # League of Legends client's current version (might not be up-to-date)

items_data = requests.get('http://ddragon.leagueoflegends.com/cdn/' + CLIENT_VERSION + '/data/en_US/item.json').json()
champions_data = requests.get('http://ddragon.leagueoflegends.com/cdn/' + CLIENT_VERSION + '/data/en_US/champion.json').json()

# ---

mobafire_items_map = {} # Matches a Mobafire item's name to it's corresponding ID

for id_, item_data in items_data['data'].items():
	# Mobafire's trinkets doesn't have ' (Trinket)' in their name so we remove it
	# e.g.: 'Warding Totem (Trinket)' [LoL] -> 'Warding Totem' [Mobafire]
	name = item_data['name'].replace(' (Trinket)', '')

	mobafire_items_map[name] = id_

# ---

def get_champion_id(champion_name):
	"""
		Matches a champion's name to it's corresponding ID
		Compares the champion's name to it's corresponding database name and ID (case insensitive)
		Returns 0 if no corresponding champion was found
	"""
	if champion_name:
		for champion in champions_data['data'].values():
			if champion_name.lower() == champion['id'].lower() or champion_name.lower() == champion['name'].lower():
				return int(champion['key'])

	return 0

# ---

class TranslateException(Exception):
	def __init__(self, message):
		super().__init__(message)

class Translator(ABC):
	def __init__(self, set_name, url):
		self.set_name = set_name # In-game item set name
		self.url = url # URL of the build to translate

	def _validate_input(self):
		"""
			Validates the given inputs and fetches the resource at `url`
			Will store the response in the `resp` attribute
			Raises a `TranslateException` if an error occurs
		"""

		if len(self.set_name) > 75:
			raise TranslateException("The maximum length of an item set's name is 75 characters")

		self.resp = requests.get(self.url)

		if self.resp.status_code != 200:
			raise TranslateException("Could not reach {}. Status code: {}".format(self.url, self.resp.status_code))

	@abstractmethod
	def _translate_build(self):
		"""
			Translates the build's data
			Must store the corresponding champion ID in the `champion_id` attribute
			Must store the build's item blocks in the `blocks` attribute
		"""

		pass

	def generate_item_set(self):
		"""
			Generates the corresponding JSON item set's data
			Will call `_validate_input` and `_translate_build`
			No input sanitizing is done here
			Returns the item set as a JSON string
		"""

		self._validate_input()
		self._translate_build()

		item_set = {
			'associatedChampions': [self.champion_id],
			'associatedMaps': [],
			'title': self.set_name,
			'blocks': self.blocks,
		}

		return json.dumps(item_set)

class MobafireTranslator(Translator):
	REGEX = r'((http|https):\/\/)?(www\.)?mobafire\.com\/league-of-legends\/build\/[A-Za-z0-9-]+-[0-9]{6}'

	def __init__(self, set_name, url, build_index):
		super().__init__(set_name, url)

		if build_index is None:
			build_index = 0

		self.build_index = build_index

	def _validate_input(self):
		if not re.match(MobafireTranslator.REGEX, self.url):
			raise TranslateException("Given URL does not match a MOBAfire guide URL")

		super()._validate_input()

	def _translate_build(self):
		soup = BeautifulSoup(self.resp.text, 'html.parser')

		champion_name = soup.find('div', class_='title').find('h3').text
		self.champion_id = get_champion_id(champion_name)

		if self.champion_id == 0:
			raise TranslateException("Champion not found in database: <{}>".format(champion_name))

		builds = soup.find_all('div', class_='view-guide__build')

		if self.build_index >= len(builds):
			self.build_index = 0

		self.blocks = []
		self.outdated_items = set()

		for block_div in builds[self.build_index].find('div', class_='view-guide__build__items').find('div', class_='collapseBox').find_all('div', class_='view-guide__items'):
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
						jgl_item_name = jgl_item_name.group()
						jgl_item_id = mobafire_items_map[jgl_item_name]

						jgl_enchantment = 'Enchantment: ' + jgl_enchantment.group()

						"""
							Jungle enchantments are treated differently because in the League of Legends' items database, enchanted jungle items have their own IDs
							but are named the same (e.g.: whether it is Skirmisher's Sabre or Stalker's Blade with 'Warrior' enchantment will be named
							'Enchantment: Warrior', but with a different ID). The only way of getting the right jungle item is to check from which items the
							enchanted jungle item was crafted, that's what we do here with the 'from' dictionary, containing the items from which one was crafted
						"""

						for id_, item_data in items_data['data'].items():
							if item_data['name'] != jgl_enchantment:
								continue

							if item_data.get('from'):
								# If the enchanted jungle item was crafted from the right jungle item
								if jgl_item_id in item_data['from']:
									# Note: 'id' has to be a str and 'count' an int
									block['items'].append({'id': id_, 'count': count})
									break

						continue

				try:
					# Note: 'id' has to be a str and 'count' an int
					block['items'].append({'id': mobafire_items_map[item_name], 'count': count})

					# If this item exists in ARAM then add it too (Quick Charge items)
					# so that if we play ARAM with this set, the item still appears
					aram_item = item_name + ' (Quick Charge)'

					if aram_item in mobafire_items_map.keys():
						block['items'].append({'id': mobafire_items_map[aram_item], 'count': count})
				except KeyError as ex:
					self.outdated_items.add(ex.args[0])
					continue

			self.blocks.append(block)

class MobalyticsTranslator(Translator):
	REGEX = r'((http|https):\/\/)?app\.mobalytics\.gg\/champions\/[A-Za-z]+\/build'

	def __init__(self, set_name, url, build_name=None):
		super().__init__(set_name, url)
		self.build_name = build_name

	def _validate_input(self):
		if not re.match(MobalyticsTranslator.REGEX, self.url):
			raise TranslateException("Given URL does not match a Mobalytics guide URL")

		super()._validate_input()

	def _translate_build(self):
		champion_name = self.url.split('/')[-2]
		self.champion_id = get_champion_id(champion_name)

		if self.champion_id == 0:
			raise TranslateException("Champion not found in database: <{}>".format(champion_name))

		self.resp = requests.get('https://api.mobalytics.gg/lol/champions/v1/meta', params={'name': champion_name.lower()})

		if self.resp.status_code != 200:
			raise TranslateException("Could not reach this Mobalytics build's data. Status code: {}".format(self.resp.status_code))

		data = self.resp.json()
		build = None

		if self.build_name:
			for role in data['data']['roles']:
				for temp in role['builds']:
					if temp['name'].lower() == self.build_name.lower():
						build = temp
						break
		else:
			build = data['data']['roles'][0]['builds'][0]

		self.blocks = []

		if not build:
			raise TranslateException("Could not retrieve data for this build")

		for name, items in build['items']['general'].items():
			block = {}

			if name == 'start':
				block['type'] = "Starter"
			elif name == 'early':
				block['type'] = "Early items"
			elif name == 'core':
				block['type'] = "Core items"
			elif name == 'full':
				block['type'] = "Full build"
			else:
				block['type'] = "???"

			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""

			counter = collections.Counter(items)
			block['items'] = []

			for id_, count in dict(counter).items():
				block['items'].append({'id': id_, 'count': count})

			if name == 'start':
				self.blocks.insert(0, block)
			else:
				self.blocks.append(block)

		for situational in build['items']['situational']:
			block = {}
			block['type'] = "Situational - " + situational['name']
			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""

			counter = collections.Counter(situational['build'])
			block['items'] = []

			for id_, count in dict(counter).items():
				block['items'].append({'id': id_, 'count': count})

			self.blocks.append(block)

class OpggTranslator(Translator):
	REGEX = r'((http|https):\/\/)?((www|na)?\.)?op\.gg\/champion\/[A-Za-z]+\/statistics\/(top|jungle|mid|bot|support)'

	def __init__(self, set_name, url):
		super().__init__(set_name, url)

	def _validate_input(self):
		if not re.match(OpggTranslator.REGEX, self.url):
			raise TranslateException("Invalid OP.GG build URL")

		super()._validate_input()

	def _translate_build(self):
		champion_name = self.url.split('/')[-3].lower()
		self.champion_id = get_champion_id(champion_name)

		if self.champion_id == 0:
			raise TranslateException("Champion not found in database: <{}>".format(champion_name))

		soup = BeautifulSoup(self.resp.text, 'html.parser')
		rows = soup.find_all('table', class_='champion-overview__table')[1].tbody.find_all('tr')

		block_title = str()

		block_index = 1
		boots_index = int()

		self.blocks = []

		for index, row in enumerate(rows):
			block = {}

			if len(row['class']) == 2 and row['class'][1] == 'champion-overview__row--first':
				block_title = row.th.text

				if block_title == "Boots":
					boots_index = index
					break

				block_index = 1

			block['type'] = block_title + " #" + str(block_index)
			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""
			block['items'] = []

			for item in row.td.ul.find_all('li', class_=['champion-stats__list__item', 'tip', 'tpd-delegation-uid-1']):
				id_ = item.img['src'].split('/')[-1].split('.png')[0]
				block['items'].append({'id': id_, 'count': 1})

			self.blocks.append(block)
			block_index += 1

		block = {}
		block['type'] = "Boots"
		block['showIfSummonerSpell'] = ""
		block['hideIfSummonerSpell'] = ""
		block['items'] = []

		for row in rows[boots_index:]:
			for item in row.td.ul.find_all('li', class_=['champion-stats__list__item', 'tip', 'tpd-delegation-uid-1']):
				id_ = item.img['src'].split('/')[-1].split('.png')[0]
				block['items'].append({'id': id_, 'count': 1})

		self.blocks.append(block)

class ChampionggTranslator(Translator):
	REGEX = r'((http|https):\/\/)?(www\.)?champion\.gg\/champion\/[A-Za-z]+\/(Top|Jungle|Middle|ADC|Support)'

	def __init__(self, set_name, url):
		super().__init__(set_name, url)

	def _validate_input(self):
		if not re.match(ChampionggTranslator.REGEX, self.url):
			raise TranslateException("Invalid Champion.gg build URL")

		super()._validate_input()

	def _translate_build(self):
		champion_name = self.url.split('/')[-2].lower()
		self.champion_id = get_champion_id(champion_name)

		if self.champion_id == 0:
			raise TranslateException("Champion not found in database: <{}>".format(champion_name))

		soup = BeautifulSoup(self.resp.text, 'html.parser')

		sections = soup.find_all('div', class_='champion-area')[1].find_all('div', class_='col-xs-12 col-sm-12 col-md-6')[1].find_all('div', class_=['col-xs-12', 'col-sm-12'])
		sections.reverse()

		self.blocks = []

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
					id_ = a.img['src'].split('/')[-1].split('.')[0]
					block['items'].append({'id': id_, 'count': 1})

				self.blocks.append(block)
