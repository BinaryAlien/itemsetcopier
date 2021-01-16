from itemsetcopier import SET_NAME_MAX_LENGTH, Translator, ReturnCode, translate
import unittest

class MobafireTest(unittest.IsolatedAsyncioTestCase):
	async def _test(self, set_name, url, build_index, expected_code):
		res = await translate(Translator.MOBAFIRE, set_name=set_name, url=url, build_index=build_index)
		self.assertEqual(res['code'], expected_code)

	async def test_translator(self):
		# Valid inputs
		await self._test("Jax Top", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', None, ReturnCode.CODE_OK)
		await self._test("Jax Top", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, ReturnCode.CODE_OK)
		await self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 2, ReturnCode.CODE_OK)
		await self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', "2", ReturnCode.CODE_OK)
		await self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 99999, ReturnCode.CODE_OK)
		await self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', -99999, ReturnCode.CODE_OK)
		await self._test("Jax Top", 'www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, ReturnCode.CODE_OK)

		# Invalid set name
		await self._test("", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, ReturnCode.ERR_SET_NAME_LENGTH)
		await self._test(('t' * (SET_NAME_MAX_LENGTH + 1)), 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, ReturnCode.ERR_SET_NAME_LENGTH)

		# Invalid URL
		await self._test("Jax Top", 'https://www.google.com', 1, ReturnCode.ERR_OTHER)
		await self._test("Jax Top", 'https://https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, ReturnCode.ERR_OTHER)

		# Other
		await self._test(123, 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', 1, ReturnCode.ERR_INVALID_PARAM)
		await self._test(None, 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', None, ReturnCode.ERR_INVALID_PARAM)
		await self._test("Jax Top", 123, 1, ReturnCode.ERR_INVALID_PARAM),
		await self._test("Jax Top", None, 1, ReturnCode.ERR_INVALID_PARAM),
		await self._test("Jax Jgl", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-503356', "abc", ReturnCode.ERR_INVALID_PARAM)
		await self._test("Jax Top", 'https://www.mobafire.com/league-of-legends/build/10-13-ph45s-in-depth-guide-to-jax-the-grandmaster-000000', 1, ReturnCode.ERR_REMOTE_FAIL)

class MobalyticsTest(unittest.IsolatedAsyncioTestCase):
	async def _test(self, champion_key, champion_name, role, expected_code):
		res = await translate(Translator.MOBALYTICS, champion_key=champion_key, champion_name=champion_name, role=role)
		self.assertEqual(res['code'], expected_code)

	async def test_translator(self):
		# Valid inputs
		await self._test(None, 'Ahri', 'mid', ReturnCode.CODE_OK)
		await self._test(103, None, 'mid', ReturnCode.CODE_OK)
		await self._test(103, 'Doesnt matter here', 'mid', ReturnCode.CODE_OK)
		await self._test(None, 'AhRi', 'mid', ReturnCode.CODE_OK)
		await self._test(None, 'AhRi', 'MiD', ReturnCode.CODE_OK)
		await self._test(103, None, 'MiD', ReturnCode.CODE_OK)
		await self._test("103", None, 'mid', ReturnCode.CODE_OK)
		await self._test("103", 'Doesnt matter here', 'mid', ReturnCode.CODE_OK)
		await self._test("103", None, 'MiD', ReturnCode.CODE_OK)

		# Invalid champion
		await self._test(None, 'ttttt', 'mid', ReturnCode.ERR_INVALID_CHAMP)
		await self._test(99999, None, 'mid', ReturnCode.ERR_INVALID_CHAMP)
		await self._test(99999, 'Ahri', 'mid', ReturnCode.ERR_INVALID_CHAMP)

		# Invalid role
		await self._test(None, 'Ahri', 'ttttt', ReturnCode.ERR_INVALID_PARAM)

		# Other
		await self._test(None, None, 'mid', ReturnCode.ERR_INVALID_PARAM)
		await self._test("abc", None, 'mid', ReturnCode.ERR_INVALID_PARAM)
		await self._test(None, 123, 'mid', ReturnCode.ERR_INVALID_PARAM)
		await self._test(None, 'Ahri', 123, ReturnCode.ERR_INVALID_PARAM)
		await self._test(None, 'Ahri', None, ReturnCode.ERR_INVALID_PARAM)

class OpggTest(unittest.IsolatedAsyncioTestCase):
	async def _test(self, set_name, champion_key, champion_name, role, expected_code):
		res = await translate(Translator.OPGG, set_name=set_name, champion_key=champion_key, champion_name=champion_name, role=role)
		self.assertEqual(res['code'], expected_code)

	async def test_translator(self):
		# Valid inputs
		await self._test("Graves Jgl", None, 'Graves', 'jungle', ReturnCode.CODE_OK)
		await self._test("Graves Jgl", 104, None, 'jungle', ReturnCode.CODE_OK)
		await self._test("Graves Jgl", 104, 'Doesnt matter here', 'jungle', ReturnCode.CODE_OK)
		await self._test("Graves Jgl", "104", None, 'jungle', ReturnCode.CODE_OK)
		await self._test("Graves Jgl", "104", 'Doesnt matter here', 'jungle', ReturnCode.CODE_OK)

		# Invalid set name
		await self._test("", None, 'Graves', 'jungle', ReturnCode.ERR_SET_NAME_LENGTH)
		await self._test(('t' * (SET_NAME_MAX_LENGTH + 1)), None, 'Graves', 'jungle', ReturnCode.ERR_SET_NAME_LENGTH)

		# Invalid champion
		await self._test("Graves Jgl", None, 'ttttt', 'jungle', ReturnCode.ERR_INVALID_CHAMP)
		await self._test("Graves Jgl", 99999, None, 'jungle', ReturnCode.ERR_INVALID_CHAMP)
		await self._test("Graves Jgl", 99999, 'Graves', 'jungle', ReturnCode.ERR_INVALID_CHAMP)

		# Invalid role
		await self._test("Graves Jgl", 'Graves', None, 'ttttt', ReturnCode.ERR_INVALID_PARAM)

		# Other
		await self._test(None, 'Graves', None, 'jungle', ReturnCode.ERR_INVALID_PARAM)
		await self._test(123, 'Graves', None, 'jungle', ReturnCode.ERR_INVALID_PARAM)
		await self._test("Graves Jgl", "abc", None, 'jungle', ReturnCode.ERR_INVALID_PARAM)
		await self._test("Graves Jgl", None, 123, 'jungle', ReturnCode.ERR_INVALID_PARAM)
		await self._test("Graves Jgl", None, None, 'jungle', ReturnCode.ERR_INVALID_PARAM)
		await self._test("Graves Jgl", None, 'Graves', 123, ReturnCode.ERR_INVALID_PARAM)
		await self._test("Graves Jgl", None, 'Graves', None, ReturnCode.ERR_INVALID_PARAM)

if __name__ == '__main__':
	unittest.main()
