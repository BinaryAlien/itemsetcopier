import itemsetcopier
import unittest

class MobafireTest(unittest.TestCase):
	def test_translator(self):
		# Valid inputs

		set_name = "Graves Jgl"
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL

		set_name = "Graves Jgl"
		url = "https://google.com/"
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Server error

		set_name = "Graves Jgl"
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-000000"
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_REMOTE)

		# Invalid inputs 1

		set_name = None
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 2

		set_name = int()
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 3

		set_name = "Graves Jgl"
		url = None
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 4

		set_name = "Graves Jgl"
		url = int()
		build_index = 0

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 5

		set_name = "Graves Jgl"
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = str()

		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

class MobalyticsTest(unittest.TestCase):
	def test_translator(self):
		# Valid inputs 1

		champion_name = "Ahri"
		champion_key = None
		role_name = "mid"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Valid inputs 2

		champion_name = "LuX"
		champion_key = None
		role_name = "mid"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Valid inputs 3

		champion_name = "does not matter if champion_key is given"
		champion_key = 36 # Dr. Mundo
		role_name = "top"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)

		# Invalid inputs 1

		champion_name = None
		champion_key = None
		role_name = "mid"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 2

		champion_name = int()
		champion_key = None
		role_name = "mid"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 3

		champion_name = "does not matter if champion_key is given"
		champion_key = str()
		role_name = "mid"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 4

		champion_name = "Lux"
		champion_key = None
		role_name = "jungle"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 5

		champion_name = "Lux"
		champion_key = None
		role_name = "tttttttttttttttttttttt"

		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

class OpggTest(unittest.TestCase):
	def test_translator(self):
		# Valid inputs

		set_name = "Graves Jgl"
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL

		set_name = "Graves Jgl"
		url = "https://google.com"

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Invalid champion

		set_name = "Graves Jgl"
		url = "https://www.op.gg/champion/tttttttttttttttttttttt/statistics/jungle"

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_CHAMPION)


		# Invalid inputs 1

		set_name = None
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 2

		set_name = int()
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 3

		set_name = "Graves Jgl"
		url = None

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 4

		set_name = "Graves Jgl"
		url = int()

		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

class ChampionggTest(unittest.TestCase):
	def test_translator(self):
		# Valid inputs

		set_name = "Jinx ADC"
		url = "https://champion.gg/champion/Jinx/ADC"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://champion.gg/champion/Jinx/ADC"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL 1

		set_name = "Jinx ADC"
		url = "https://google.com"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Invalid URL 2

		set_name = "Jinx ADC"
		url = "https://champion.gg/champion/Jinx/tttttttttttttttttttttt"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Invalid champion

		set_name = "Jinx ADC"
		url = "https://champion.gg/champion/tttttttttttttttttttttt/ADC"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_CHAMPION)


		# Invalid inputs 1

		set_name = None
		url = "https://champion.gg/champion/Jinx/ADC"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 2

		set_name = int()
		url = "https://champion.gg/champion/Jinx/ADC"

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 3

		set_name = "Jinx ADC"
		url = None

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid inputs 4

		set_name = "Jinx ADC"
		url = int()

		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

if __name__ == '__main__':
	unittest.main()
