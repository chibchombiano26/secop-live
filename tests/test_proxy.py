"""No-network unit tests: SoQL escaping, paging math, cache TTL."""
import time
import unittest

from api import socrata
from api.cache import cached, last_hit


class TestSoql(unittest.TestCase):
    def test_esc(self):
        self.assertEqual(socrata._esc("l'hopital"), "l''hopital")

    def test_like(self):
        self.assertIn("upper(entidad) like '%HOSPITAL%'",
                      socrata._like("entidad", "hospital"))

    def test_page_next(self):
        p = socrata._page([1, 2], 2, 0)
        self.assertEqual(p["next_offset"], 2)
        self.assertIsNone(p["prev_offset"])

    def test_page_last(self):
        p = socrata._page([1], 2, 4)
        self.assertIsNone(p["next_offset"])
        self.assertEqual(p["prev_offset"], 2)

    def test_words_any(self):
        q = socrata._words_any(["nombre_archivo", "descripci_n"],
                               "suministro alimentos")
        self.assertIn("upper(nombre_archivo) like '%SUMINISTRO%'", q)
        self.assertIn("upper(descripci_n) like '%ALIMENTOS%'", q)
        self.assertIn(" AND ", q)


class TestCache(unittest.TestCase):
    def test_hit_and_bypass(self):
        calls = []

        @cached
        def f(x, fresh=False):
            calls.append(x)
            return x * 2

        self.assertEqual(f(2), 4)
        self.assertFalse(last_hit.get(True))
        self.assertEqual(f(2), 4)
        self.assertTrue(last_hit.get(False))
        self.assertEqual(len(calls), 1)
        self.assertEqual(f(2, fresh=True), 4)
        self.assertFalse(last_hit.get(True))
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
