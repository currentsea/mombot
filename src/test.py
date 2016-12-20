import unittest

from mombot import MomBot

class PrimesTestCase(unittest.TestCase):
    """Tests for `primes.py`."""
    def setUp(self):
        self.mom = MomBot()

    def test_get_banhammer_headers(self):
        headers = self.mom.get_banhammer_headers()
        self.assertTrue(headers != None)
        self.assertTrue('X-Ban-Hammer-Key' in headers)
        self.assertTrue('X-Ban-Hammer-Secret' in headers)
        self.assertTrue('Content-Type' in headers)

if __name__ == '__main__':
    unittest.main()