import unittest
from ledger.refund import refund_cents


class Refund(unittest.TestCase):
    def test_refund_is_negated_charge(self):self.assertEqual(refund_cents('0.29'),-29)
