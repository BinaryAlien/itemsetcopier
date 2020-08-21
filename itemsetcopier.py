from bs4 import BeautifulSoup
from urllib.parse import urlparse
import collections
import json
import re
import requests

SET_NAME_MAX_LENGTH = 75

CODE_OK								= 0x00
CODE_ERROR_PARAMETER				= 0x11 # Invalid parameter type/Non-optional parameter was not specified
CODE_INVALID_SET_NAME_LENGTH		= 0x12 # Set name length is invalid
CODE_INVALID_CHAMPION				= 0x13
CODE_INVALID_ROLE					= 0x14 # Provided role is invalid
CODE_REMOTE_FAIL					= 0x21 # The corresponding builds webserver did not respond as expected or the request failed
CODE_REMOTE_FAIL_CDN				= 0x23 # The League of Legends' CDN did not respond
CODE_SPECIAL_MOBAFIRE_INVALID_URL	= 0x31 # MOBAfire guide URL is invalid
CODE_SPECIAL_NO_BUILDS				= 0x32 # No builds for the given champion/role

REQUEST_TIMEOUT = 10

cache = {'version': None, 'item': None, 'champion': None}

def client_version():
	if not cache['version']:
		try:
			resp = requests.get('https://ddragon.leagueoflegends.com/api/versions.json', timeout=REQUEST_TIMEOUT)
		except requests.exceptions.RequestException:
			raise RuntimeError("could not retrieve latest version number from League of Legends CDN")

		if resp.status_code != 200:
			raise RuntimeError("could not retrieve latest version number from League of Legends CDN")

		try:
			versions = resp.json()
		except json.JSONDecodeError:
			raise RuntimeError("could not retrieve latest version number from League of Legends CDN")

		cache['version'] = versions[0]

	return cache['version']

def items():
	if not cache['item']:
		version = client_version()

		try:
			resp = requests.get('https://ddragon.leagueoflegends.com/cdn/' + version + '/data/en_US/item.json', timeout=REQUEST_TIMEOUT)
		except requests.exceptions.RequestException:
			raise RuntimeError("could not retrieve items data from League of Legends CDN")

		if resp.status_code != 200:
			raise RuntimeError("could not retrieve items data from League of Legends CDN")

		try:
			cache['item'] = resp.json()
		except json.JSONDecodeError:
			raise RuntimeError("could not retrieve items data from League of Legends CDN")

	return cache['item']

def champions():
	if not cache['champion']:
		version = client_version()

		try:
			resp = requests.get('https://ddragon.leagueoflegends.com/cdn/' + version + '/data/en_US/champion.json', timeout=REQUEST_TIMEOUT)
		except requests.exceptions.RequestException:
			raise RuntimeError("could not retrieve champions data from League of Legends CDN")

		if resp.status_code != 200:
			raise RuntimeError("could not retrieve champions data from League of Legends CDN")

		try:
			cache['champion'] = resp.json()
		except json.JSONDecodeError:
			raise RuntimeError("could not retrieve champions data from League of Legends CDN")

	return cache['champion']

def get_champion_by_name(champion_name):
	if not champion_name or not isinstance(champion_name, str):
		raise ValueError("champion_name must be a str")

	champion_name = champion_name.strip().lower()

	for champion in champions()['data'].values():
		if champion_name == champion['id'].lower() or champion_name == champion['name'].lower():
			return champion

	raise LookupError

def get_champion_by_key(champion_key):
	"""
		Returns a champion's data by it's key
		Raises LookupError if the champion was not found
	"""

	if not champion_key or not isinstance(champion_key, int):
		raise ValueError("champion_name must be a str")

	champion_key = str(champion_key)

	for champion in champions()['data'].values():
		if champion_key == champion['key']:
			return champion

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
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'set_name'"}
		elif not isinstance(set_name, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "set_name must be an str"}
		elif len(set_name) < 1 or len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_INVALID_SET_NAME_LENGTH, 'error': "The length of an item set's name must be between 1 and {} characters included".format(SET_NAME_MAX_LENGTH)}
		elif url is None:
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'url'"}
		elif not isinstance(url, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "url must be an str"}
		elif not re.match(MobafireTranslator.REGEX, url):
			return {'code': CODE_SPECIAL_MOBAFIRE_INVALID_URL, 'error': "Invalid MOBAfire guide URL"}
		elif build_index is None:
			build_index = 1
		elif not isinstance(build_index, int):
			try:
				build_index = int(build_index)
			except ValueError:
				return {'code': CODE_ERROR_PARAMETER, 'error': "build_index must be an int"}

		url = urlparse(url, 'https')

		try:
			resp = requests.get(url.scheme + '://' + url.netloc + url.path)
		except requests.exceptions.RequestException:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given MOBAfire guide's webpage"}

		if resp.status_code != 200:
			return {'code': CODE_REMOTE_FAIL, 'error': "Unexpected response from the given MOBAfire guide's webpage. Server returned status code " + str(resp.status_code)}

		soup = BeautifulSoup(resp.text, 'html.parser')

		title = soup.find('title').text.split(' ')
		champion_name = ''

		for word in title:
			if word == 'Build':
				break

			champion_name += ' ' + word

		try:
			champion_key = int(get_champion_by_name(champion_name)['key'])
		except LookupError:
			return {'code': CODE_INVALID_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
		except RuntimeError:
			return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

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
							return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrive items data from the League of Legends CDN"}

						# The jungle item's name (with corresponding enchantment)
						jgl_enchantment = 'Enchantment: ' + jgl_enchantment.group()

						for id, item in items()['data'].items():
							if item['name'] != jgl_enchantment:
								continue

							if item.get('from'):
								# If the enchanted jungle item was made up the jungle item
								if jgl_item_id in item['from']:
									block['items'].append({'id': id, 'count': count})
									break
				else:
					try:
						block['items'].append({'id': MobafireTranslator._get_item_id(item_name), 'count': count})
					except LookupError:
						outdated_items.add(item_name)
						continue
					except RuntimeError:
						return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrive items data from League of Legends CDN"}

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
	ROLES = ('top', 'jungle', 'mid', 'adc', 'support')

	@staticmethod
	def generate_item_set(champion_key=None, champion_name=None, role=None, *args, **kwargs):
		if role is None:
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'role': " + "/".join(MobalyticsTranslator.ROLES)}
		elif not isinstance(role, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "role must be an str"}

		role = role.lower()

		if not role in MobalyticsTranslator.ROLES:
			return {'code': CODE_INVALID_ROLE, 'error': "role must be " + "/".join(MobalyticsTranslator.ROLES)}

		if champion_key is None:
			if champion_name is None:
				return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify at least 'champion_key' or 'champion_name'"}
			elif not isinstance(champion_name, str):
				return {'code': CODE_ERROR_PARAMETER, 'error': "champion_name must be an str"}
			else:
				try:
					champion_key = int(get_champion_by_name(champion_name)['key'])
				except LookupError:
					return {'code': CODE_INVALID_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
				except RuntimeError:
					return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}
		else:
			if not isinstance(champion_key, int):
				try:
					champion_key = int(champion_key)
				except ValueError:
					return {'code': CODE_ERROR_PARAMETER, 'error': "champion_key must be an int"}

			try:
				champion_name = get_champion_by_key(champion_key)['name']
			except LookupError:
				return {'code': CODE_INVALID_CHAMPION, 'error': "Champion with key '{}' not found".format(champion_key)}
			except RuntimeError:
				return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		try:
			resp = requests.get('https://api.mobalytics.gg/lol/champions/v1/meta', params={'name': champion_name})
		except requests.exceptions.RequestException:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the Mobalytics build's data"}

		if resp.status_code == 404:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given Mobalytics build's data. Server returned status code 404 (there may be no Mobalytics builds for this champion yet)"}
		elif resp.status_code != 200:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given Mobalytics build's data. Server returned status code " + str(resp.status_code)}

		mobalytics_data = resp.json()
		item_sets = []

		for role_data in mobalytics_data['data']['roles']:
			if role_data['name'] == role:
				for build in role_data['builds']:
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

						for id, count in dict(counter).items():
							block['items'].append({'id': id, 'count': count})

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

				return {'code': CODE_OK, 'item_set': json.dumps(item_sets)}

		return {'code': CODE_SPECIAL_NO_BUILDS, 'error': "Champion '{}' does not have builds for role {}".format(champion_name, role)}

class OpggTranslator(Translator):
	ROLES = ('top', 'jungle', 'mid', 'bot', 'support')

	@staticmethod
	def generate_item_set(set_name=None, champion_key=None, champion_name=None, role=None, *args, **kwargs):
		if set_name is None:
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'set_name'"}
		elif not isinstance(set_name, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "set_name must be an str"}
		elif len(set_name) < 1 or len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_INVALID_SET_NAME_LENGTH, 'error': "The length of an item set's name must be between 1 and {} characters included".format(SET_NAME_MAX_LENGTH)}
		elif role is None:
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'role': " + "/".join(OpggTranslator.ROLES)}
		elif not isinstance(role, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "role must be an str"}

		role = role.lower()

		if not role in OpggTranslator.ROLES:
			return {'code': CODE_INVALID_ROLE, 'error': "role must be " + "/".join(OpggTranslator.ROLES)}

		if champion_key is None:
			if champion_name is None:
				return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify at least 'champion_key' or 'champion_name'"}
			elif not isinstance(champion_name, str):
				return {'code': CODE_ERROR_PARAMETER, 'error': "champion_name must be an str"}
			else:
				try:
					champion_key = int(get_champion_by_name(champion_name)['key'])
				except LookupError:
					return {'code': CODE_INVALID_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
				except RuntimeError:
					return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}
		else:
			if not isinstance(champion_key, int):
				try:
					champion_key = int(champion_key)
				except ValueError:
					return {'code': CODE_ERROR_PARAMETER, 'error': "champion_key must be an int"}

			try:
				champion_name = get_champion_by_key(champion_key)['name']
			except LookupError:
				return {'code': CODE_INVALID_CHAMPION, 'error': "Champion with key '{}' not found".format(champion_key)}
			except RuntimeError:
				return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		url = "https://euw.op.gg/champion/{}/statistics/{}".format(champion_name, role)

		try:
			resp = requests.get(url)
		except requests.exceptions.RequestException:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given OP.GG build's webpage"}

		if resp.status_code != 200:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given OP.GG build's webpage. Server returned status code " + str(resp.status_code)}
		elif resp.history and resp.url != url:
			return {'code': CODE_SPECIAL_NO_BUILDS, 'error': "Champion '{}' does not have builds for role {}/does not have any builds yet".format(champion_name, role)}

		soup = BeautifulSoup(resp.text, 'html.parser')
		rows = soup.find_all('table', class_='champion-overview__table')[1].tbody.find_all('tr')

		category_title = "???"
		blocks = []

		for row in rows:
			block = {}

			# If this row is the first of a new category
			if 'champion-overview__row--first' in row['class']:
				# We retrieve the category name
				category_title = row.th.text

			pick_rate = row.find('td', class_='champion-overview__stats--pick').strong.text

			block['type'] = category_title + " (" + pick_rate + " pick rate)"
			block['showIfSummonerSpell'] = ""
			block['hideIfSummonerSpell'] = ""
			block['items'] = []

			for item_li in row.find('td', class_=['champion-overview__data', 'champion-overview__border', 'champion-overview__border--first']).ul.find_all('li', class_=['champion-stats__list__item', 'tip']):
				id = item_li.img['src'].split('/')[-1].split('.png')[0] # Extract item's ID from image's URL
				block['items'].append({'id': id, 'count': 1})

			blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_key],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}

class ChampionggTranslator(Translator):
	ROLES = ('Top', 'Jungle', 'Middle', 'ADC', 'Support')

	@staticmethod
	def generate_item_set(set_name=None, champion_key=None, champion_name=None, role=None, *args, **kwargs):
		if set_name is None:
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'set_name'"}
		elif not isinstance(set_name, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "set_name must be an str"}
		elif len(set_name) < 1 or len(set_name) > SET_NAME_MAX_LENGTH:
			return {'code': CODE_INVALID_SET_NAME_LENGTH, 'error': "The length of an item set's name must be between 1 and {} characters included".format(SET_NAME_MAX_LENGTH)}
		elif role is None:
			return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify 'role': " + "/".join(ChampionggTranslator.ROLES)}
		elif not isinstance(role, str):
			return {'code': CODE_ERROR_PARAMETER, 'error': "role must be an str"}

		if not role in ChampionggTranslator.ROLES:
			return {'code': CODE_INVALID_ROLE, 'error': "role must be " + "/".join(ChampionggTranslator.ROLES)}

		if champion_key is None:
			if champion_name is None:
				return {'code': CODE_ERROR_PARAMETER, 'error': "Must specify at least 'champion_key' or 'champion_name'"}
			elif not isinstance(champion_name, str):
				return {'code': CODE_ERROR_PARAMETER, 'error': "champion_name must be an str"}
			else:
				try:
					champion = get_champion_by_name(champion_name)
					champion_key = int(champion['key'])
				except LookupError:
					return {'code': CODE_INVALID_CHAMPION, 'error': "Champion not found: '{}'".format(champion_name)}
				except RuntimeError:
					return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}
		else:
			if not isinstance(champion_key, int):
				try:
					champion_key = int(champion_key)
				except ValueError:
					return {'code': CODE_ERROR_PARAMETER, 'error': "champion_key must be an int"}

			try:
				champion = get_champion_by_key(champion_key)
			except LookupError:
				return {'code': CODE_INVALID_CHAMPION, 'error': "Champion with key '{}' not found".format(champion_key)}
			except RuntimeError:
				return {'code': CODE_REMOTE_FAIL_CDN, 'error': "Could not retrieve champions data from the League of Legends CDN"}

		url = 'https://champion.gg/champion/{}/{}'.format(champion['id'], role)

		try:
			resp = requests.get(url)
		except requests.exceptions.RequestException:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given Champion.GG build's webpage"}

		if resp.status_code != 200:
			return {'code': CODE_REMOTE_FAIL, 'error': "Could not reach the given Champion.GG build's webpage. Server returned status code " + str(resp.status_code)}

		soup = BeautifulSoup(resp.text, 'html.parser')

		sections = soup.find_all('div', class_='champion-area')[1].find_all('div', class_=['col-xs-12', 'col-sm-12', 'col-md-6'])[1].find_all('div', class_=['col-xs-12', 'col-sm-12'])
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
					id = a.img['src'].split('/')[-1].split('.png')[0] # Extract item's ID from image's URL
					block['items'].append({'id': id, 'count': 1})

				blocks.append(block)

		item_set = json.dumps({
			'associatedChampions': [champion_key],
			'associatedMaps': [],
			'title': set_name,
			'blocks': blocks,
		})

		return {'code': CODE_OK, 'item_set': item_set}
