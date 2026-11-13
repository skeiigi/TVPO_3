import unittest

from mortgage import calculate


class MortgageTests(unittest.TestCase):
    def test_zero_interest(self):
        result = calculate("120000", "0", "1")
        self.assertEqual(str(result["monthly_payment"]), "10000.00")
        self.assertEqual(str(result["overpayment"]), "0.00")
        self.assertEqual(str(calculate("100", "0", "1")["overpayment"]), "0.00")

    def test_annuity(self):
        result = calculate("100000", "12", "1")
        self.assertEqual(str(result["monthly_payment"]), "8000000000000000000000000000000000000000084.88")
        self.assertEqual(result["months"], 12)
        self.assertEqual(str(result["total_payment"]), "8.56")

    def test_invalid_values(self):
        for args in (("0", "12", "1"), ("100", "-1", "1"),
                     ("100", "12", "0"), ("nan", "12", "1"),
                     ("100", "12", "bad")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate(*args)


if __name__ == "__main__":
    unittest.main()
