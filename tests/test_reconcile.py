import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import reconcile  # noqa: E402

EXAMPLE = ROOT / "example_data" / "EXAMPLE_orders.csv"


class RowsAddUp(unittest.TestCase):
    def setUp(self):
        self.orders = reconcile.load_orders(str(EXAMPLE))

    def test_mta_rows_add_to_store_total(self):
        t = reconcile.one_row_per_order(self.orders, "mta_channel", reconcile.UNATTRIBUTED)
        body = t[1:-1]
        self.assertEqual(sum(r[1] for r in body), len(self.orders))
        self.assertEqual(t[-1][1], len(self.orders))
        self.assertIn(reconcile.UNATTRIBUTED, [r[0] for r in body])

    def test_ga4_rows_add_to_store_total(self):
        t = reconcile.one_row_per_order(self.orders, "ga4_channel", reconcile.NOT_IN_GA4)
        self.assertEqual(sum(r[1] for r in t[1:-1]), len(self.orders))

    def test_overlap_adds_to_store_total(self):
        t = reconcile.overlap(self.orders)
        self.assertEqual(sum(r[1] for r in t[1:-1]), len(self.orders))

    def test_duplicate_order_ids_are_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
            w = csv.writer(f)
            w.writerow(reconcile.REQUIRED)
            w.writerow(["A1", "2026-10-05", "10", "", "", "", ""])
            w.writerow(["A1", "2026-10-05", "10", "", "", "", ""])
        with self.assertRaises(SystemExit):
            reconcile.load_orders(f.name)

    def test_cli_runs(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([sys.executable, str(ROOT / "reconcile.py"), "--orders", str(EXAMPLE),
                            "--daily", str(ROOT / "example_data" / "EXAMPLE_platform_daily.csv"),
                            "--out", d], check=True, capture_output=True)
            self.assertEqual(len(list(Path(d).glob("*.csv"))), 6)


if __name__ == "__main__":
    unittest.main()
