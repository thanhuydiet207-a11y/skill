import unittest
from ledger.invoice import invoice_total


class InvoiceTotal(unittest.TestCase):
    def test_whole_amounts(self):self.assertEqual(invoice_total(['1.00','2.50']),350)
    def test_cents_are_exact(self):self.assertEqual(invoice_total(['0.29','1.10']),139)
