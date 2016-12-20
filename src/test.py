import json
import unittest
from mombot import MomBot

class PrimesTestCase(unittest.TestCase):
    """Tests for `primes.py`."""
    def setUp(self):
        self.mom = MomBot()
        self.banlist = self.load_test_banlist()

    def load_test_banlist(self):
        with open('test_data/banlist.json', 'r') as theBanListFile:
           banlist_data = json.load(theBanListFile)
        return banlist_data

    def test_get_banhammer_headers(self):
        headers = self.mom.get_banhammer_headers()
        self.assertTrue(headers != None)
        self.assertTrue('X-Ban-Hammer-Key' in headers)
        self.assertTrue('X-Ban-Hammer-Secret' in headers)
        self.assertTrue('Content-Type' in headers)

    def test_loaded_banlist(self):
        self.assertTrue(self.banlist != None)
        self.assertTrue('ban_list' in self.banlist)

    def test_get_blacklist(self):
        expected = self.get_expected_blacklist('banned_user_telegram_id')
        ban_user_list = self.mom.get_blacklist_ids(self.banlist)
        self.assertEqual(expected, ban_user_list)

    def get_expected_blacklist(self, target):
        expected = []
        for item in self.banlist['ban_list']:
            expected.append(item[target])
        return expected

    def test_get_blacklist_users(self):
        expected = []
        for item in self.banlist['ban_list']:
            if item['banned_user'] == "":
                expected.append(item['banned_user_telegram_id'])
        actual = self.mom.get_blacklist(self.banlist)
        self.assertTrue(expected, actual)

if __name__ == '__main__':
    unittest.main()