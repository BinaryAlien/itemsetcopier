import itemsetcopier
import unittest

class MobafireTest(unittest.TestCase):
	def _test(self, set_name, url, build_index, expected_code):
		res = itemsetcopier.MobafireTranslator.generate_item_set(set_name, url, build_index)
		self.assertEqual(res['code'], expected_code)

	def test_translator(self):
		# Valid inputs
		self._test("Jax Top", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', None, itemsetcopier.CODE_OK)
		self._test("Jax Top", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, itemsetcopier.CODE_OK)
		self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 2, itemsetcopier.CODE_OK)
		self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', "2", itemsetcopier.CODE_OK)
		self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 99999, itemsetcopier.CODE_OK)
		self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', -99999, itemsetcopier.CODE_OK)
		self._test("Jax Top", 'www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, itemsetcopier.CODE_OK)

		# Invalid set name
		self._test("", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, itemsetcopier.CODE_INVALID_SET_NAME_LENGTH)
		self._test(('t' * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)), 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, itemsetcopier.CODE_INVALID_SET_NAME_LENGTH)

		# Invalid URL
		self._test("Jax Top", 'https://www.google.com', 1, itemsetcopier.CODE_SPECIAL_MOBAFIRE_INVALID_URL)
		self._test("Jax Top", 'https://https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, itemsetcopier.CODE_SPECIAL_MOBAFIRE_INVALID_URL)

		# Other
		self._test(123, 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, itemsetcopier.CODE_ERROR_PARAMETER)
		self._test(None, 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', None, itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Jax Top", 123, 1, itemsetcopier.CODE_ERROR_PARAMETER),
		self._test("Jax Top", None, 1, itemsetcopier.CODE_ERROR_PARAMETER),
		self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', "abc", itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Jax Top", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-000000', 1, itemsetcopier.CODE_REMOTE_FAIL)

class MobalyticsTest(unittest.TestCase):
	def _test(self, champion_key, champion_name, role, expected_code):
		res = itemsetcopier.MobalyticsTranslator.generate_item_set(champion_key, champion_name, role)
		self.assertEqual(res['code'], expected_code)

	def test_translator(self):
		# Valid inputs
		self._test(None, 'Ahri', 'mid', itemsetcopier.CODE_OK)
		self._test(103, None, 'mid', itemsetcopier.CODE_OK)
		self._test(103, 'Doesnt matter here', 'mid', itemsetcopier.CODE_OK)
		self._test(None, 'AhRi', 'mid', itemsetcopier.CODE_OK)
		self._test(None, 'AhRi', 'MiD', itemsetcopier.CODE_OK)
		self._test(103, None, 'MiD', itemsetcopier.CODE_OK)
		self._test("103", None, 'mid', itemsetcopier.CODE_OK)
		self._test("103", 'Doesnt matter here', 'mid', itemsetcopier.CODE_OK)
		self._test("103", None, 'MiD', itemsetcopier.CODE_OK)

		# Invalid champion
		self._test(None, 'ttttt', 'mid', itemsetcopier.CODE_INVALID_CHAMPION)
		self._test(99999, None, 'mid', itemsetcopier.CODE_INVALID_CHAMPION)
		self._test(99999, 'Ahri', 'mid', itemsetcopier.CODE_INVALID_CHAMPION)

		# Invalid role
		self._test(None, 'Ahri', 'ttttt', itemsetcopier.CODE_INVALID_ROLE)

		# Other
		self._test(None, None, 'mid', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("abc", None, 'mid', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test(None, 123, 'mid', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test(None, 'Ahri', 123, itemsetcopier.CODE_ERROR_PARAMETER)
		self._test(None, 'Ahri', None, itemsetcopier.CODE_ERROR_PARAMETER)

class OpggTest(unittest.TestCase):
	def _test(self, set_name, champion_key, champion_name, role, expected_code):
		res = itemsetcopier.OpggTranslator.generate_item_set(set_name, champion_key, champion_name, role)
		self.assertEqual(res['code'], expected_code)

	def test_translator(self):
		# Valid inputs
		self._test("Graves Jgl", None, 'Graves', 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", 104, None, 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", 104, 'Doesnt matter here', 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", "104", None, 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", "104", 'Doesnt matter here', 'jungle', itemsetcopier.CODE_OK)

		# Invalid set name
		self._test("", None, 'Graves', 'jungle', itemsetcopier.CODE_INVALID_SET_NAME_LENGTH)
		self._test(('t' * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)), None, 'Graves', 'jungle', itemsetcopier.CODE_INVALID_SET_NAME_LENGTH)

		# Invalid champion
		self._test("Graves Jgl", None, 'ttttt', 'jungle', itemsetcopier.CODE_INVALID_CHAMPION)
		self._test("Graves Jgl", 99999, None, 'jungle', itemsetcopier.CODE_INVALID_CHAMPION)
		self._test("Graves Jgl", 99999, 'Graves', 'jungle', itemsetcopier.CODE_INVALID_CHAMPION)

		# Invalid role
		self._test("Graves Jgl", 'Graves', None, 'ttttt', itemsetcopier.CODE_INVALID_ROLE)

		# Other
		self._test(None, 'Graves', None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test(123, 'Graves', None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", "abc", None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, 123, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, 'Graves', 123, itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, 'Graves', None, itemsetcopier.CODE_ERROR_PARAMETER)

class ChampionggTest(unittest.TestCase):
	def _test(self, set_name, champion_key, champion_name, role, expected_code):
		res = itemsetcopier.ChampionggTranslator.generate_item_set(set_name, champion_key, champion_name, role)
		self.assertEqual(res['code'], expected_code)

	def test_translator(self):
		# Valid inputs
		self._test("Graves Jgl", None, 'Graves', 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", 104, None, 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", 104, 'Doesnt matter here', 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", "104", None, 'jungle', itemsetcopier.CODE_OK)
		self._test("Graves Jgl", "104", 'Doesnt matter here', 'jungle', itemsetcopier.CODE_OK)

		# Invalid set name
		self._test("", None, 'Graves', 'jungle', itemsetcopier.CODE_INVALID_SET_NAME_LENGTH)
		self._test(('t' * (itemsetcopier.SET_NAME_MAX_LENGTH + 1)), None, 'Graves', 'jungle', itemsetcopier.CODE_INVALID_SET_NAME_LENGTH)

		# Invalid champion
		self._test("Graves Jgl", None, 'ttttt', 'jungle', itemsetcopier.CODE_INVALID_CHAMPION)
		self._test("Graves Jgl", 99999, None, 'jungle', itemsetcopier.CODE_INVALID_CHAMPION)
		self._test("Graves Jgl", 99999, 'Graves', 'jungle', itemsetcopier.CODE_INVALID_CHAMPION)

		# Invalid role
		self._test("Graves Jgl", 'Graves', None, 'ttttt', itemsetcopier.CODE_INVALID_ROLE)

		# Other
		self._test(None, 'Graves', None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test(123, 'Graves', None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", "abc", None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, 123, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, None, 'jungle', itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, 'Graves', 123, itemsetcopier.CODE_ERROR_PARAMETER)
		self._test("Graves Jgl", None, 'Graves', None, itemsetcopier.CODE_ERROR_PARAMETER)

if __name__ == '__main__':
	unittest.main()
