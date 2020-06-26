import itemsetcopier
import unittest

class MobafireTest(unittest.TestCase):
	def test_translator(self):
		self._translator = itemsetcopier.MobafireTranslator()

		# Valid inputs

		set_name = "Graves Jgl"
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL

		set_name = "Graves Jgl"
		url = "https://google.com/"
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Server error

		set_name = "Graves Jgl"
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-000000"
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SERVER)

		# Invalid input 1

		set_name = None
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 2

		set_name = int()
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 3

		set_name = "Graves Jgl"
		url = None
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 4

		set_name = "Graves Jgl"
		url = int()
		build_index = 0

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 5

		set_name = "Graves Jgl"
		url = "https://www.mobafire.com/league-of-legends/build/graves-jungle-fallen3s-guide-to-graves-jungle-564027"
		build_index = str()

		res = self._translator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

class MobalyticsTest(unittest.TestCase):
	def test_translator(self):
		self._translator = itemsetcopier.MobalyticsTranslator()

		# Valid inputs (default build)

		set_name = "Ahri Mid"
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Valid inputs (specific build)

		set_name = "Ahri Mid"
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = "AhRi GlAcIaL MiD"

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL

		set_name = "Ahri Mid"
		url = "https://google.com"
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Invalid champion

		set_name = "Ahri Mid"
		url = "https://app.mobalytics.gg/champions/tttttttttttttttttttttt/build"
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_CHAMPION)


		# Invalid build

		set_name = "Ahri Mid"
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = "tttttttttttttttttttttt"

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_OTHER)


		# Invalid input 1

		set_name = None
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 2

		set_name = int()
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 3

		set_name = "Ahri Mid"
		url = None
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 4

		set_name = "Ahri Mid"
		url = int()
		build_name = None

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

		# Invalid input 5

		set_name = "Ahri Mid"
		url = "https://app.mobalytics.gg/champions/ahri/build"
		build_name = int()

		res = self._translator.generate_item_set(set_name, url, build_name)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

class OpggTest(unittest.TestCase):
	def test_translator(self):
		self._translator = itemsetcopier.OpggTranslator()

		# Valid inputs

		set_name = "Graves Jgl"
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL

		set_name = "Graves Jgl"
		url = "https://google.com"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)


		# Invalid champion

		set_name = "Graves Jgl"
		url = "https://www.op.gg/champion/tttttttttttttttttttttt/statistics/jungle"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_CHAMPION)


		# Invalid input 1

		set_name = None
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 2

		set_name = int()
		url = "https://www.op.gg/champion/graves/statistics/jungle"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 3

		set_name = "Graves Jgl"
		url = None

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 4

		set_name = "Graves Jgl"
		url = int()

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

class ChampionggTest(unittest.TestCase):
	def test_translator(self):
		self._translator = itemsetcopier.ChampionggTranslator()

		# Valid inputs

		set_name = "Jinx ADC"
		url = "https://champion.gg/champion/Jinx/ADC"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_OK)


		# Invalid item set name

		set_name = "t" * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)
		url = "https://champion.gg/champion/Jinx/ADC"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_SET_NAME_MAX_LENGTH)


		# Invalid URL #1

		set_name = "Jinx ADC"
		url = "https://google.com"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)

		# Invalid URL #2

		set_name = "Jinx ADC"
		url = "https://champion.gg/champion/Jinx/tttttttttttttttttttttt"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_URL)

		# Invalid champion

		set_name = "Jinx ADC"
		url = "https://champion.gg/champion/tttttttttttttttttttttt/ADC"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_CHAMPION)


		# Invalid input 1

		set_name = None
		url = "https://champion.gg/champion/Jinx/ADC"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 2

		set_name = int()
		url = "https://champion.gg/champion/Jinx/ADC"

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 3

		set_name = "Jinx ADC"
		url = None

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)


		# Invalid input 4

		set_name = "Jinx ADC"
		url = int()

		res = self._translator.generate_item_set(set_name, url)
		self.assertEqual(res['code'], itemsetcopier.CODE_ERROR_INVALID_INPUT)

if __name__ == '__main__':
	unittest.main()
