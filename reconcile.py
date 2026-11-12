"""Line up Shopify orders against what each platform and your MTA say.

Usage:
    python reconcile.py --orders example_data/EXAMPLE_orders.csv \
        [--daily example_data/EXAMPLE_platform_daily.csv] [--out example_output]

Standard library only. Python 3.9 or newer.

Input columns (orders file, one row per Shopify order):
    order_id, order_date (YYYY-MM-DD), net_sales, customer_type,
    meta_claim (click, view, or blank), google_claim (click or blank),
    ga4_channel (blank if GA4 has no record of the order),
    mta_channel (blank if the MTA could not place the order)

Outputs (CSV, one file per table):
    1_platform_claims.csv  What each platform claims, next to the store total.
                           Claims overlap, so they do not add up to the store.
    2_overlap.csv          How many orders were claimed by Meta, Google, both,
                           or neither.
    3_ga4_rows.csv         GA4 channels plus a "Not in GA4" row. Adds to the
                           store total.
    4_mta_rows.csv         MTA channels plus an "Unattributed" row. Adds to the
                           store total.
    5_claims_vs_mta.csv    Orders each platform claims next to the orders the
                           MTA placed on that platform's row.
    6_daily_ratio.csv      Platform-reported orders divided by Shopify orders,
                           per day (only with --daily).
"""
from __future__ import annotations

import argparse
import csv
from collections import OrderedDict, defaultdict
from pathlib import Path

UNATTRIBUTED = "Unattributed"
NOT_IN_GA4 = "Not in GA4"
REQUIRED = ["order_id", "order_date", "net_sales", "meta_claim", "google_claim", "ga4_channel", "mta_channel"]


def load_orders(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"{path} has no rows")
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        raise SystemExit(f"{path} is missing columns: {', '.join(missing)}")
    seen = set()
    for r in rows:
        if r["order_id"] in seen:
            raise SystemExit(f"Duplicate order_id {r['order_id']}: each Shopify order must appear once")
        seen.add(r["order_id"])
        r["net_sales"] = float(r["net_sales"] or 0)
        for c in ("meta_claim", "google_claim", "ga4_channel", "mta_channel"):
            r[c] = (r[c] or "").strip()
    return rows


def pct(part: float, whole: float) -> str:
    return f"{part / whole:.1%}" if whole else ""


def money(x: float) -> str:
    return f"{x:.2f}"


def platform_claims(orders: list[dict]) -> list[list]:
    total_n = len(orders)
    total_rev = sum(o["net_sales"] for o in orders)
    out = [["row", "orders", "net_sales", "share_of_store_orders"]]
    claims = OrderedDict([
        ("Meta (click)", [o for o in orders if o["meta_claim"] == "click"]),
        ("Meta (view)", [o for o in orders if o["meta_claim"] == "view"]),
        ("Google Ads", [o for o in orders if o["google_claim"]]),
    ])
    claimed_n = claimed_rev = 0.0
    for name, rows in claims.items():
        n, rev = len(rows), sum(o["net_sales"] for o in rows)
        claimed_n += n
        claimed_rev += rev
        out.append([name, n, money(rev), pct(n, total_n)])
    out.append(["Sum of platform claims", int(claimed_n), money(claimed_rev), pct(claimed_n, total_n)])
    out.append(["Shopify orders (store total)", total_n, money(total_rev), "100.0%"])
    return out


def overlap(orders: list[dict]) -> list[list]:
    groups = OrderedDict([("Meta and Google", 0), ("Meta only", 0), ("Google only", 0), ("Neither platform", 0)])
    rev = defaultdict(float)
    for o in orders:
        m, g = bool(o["meta_claim"]), bool(o["google_claim"])
        key = "Meta and Google" if m and g else "Meta only" if m else "Google only" if g else "Neither platform"
        groups[key] += 1
        rev[key] += o["net_sales"]
    out = [["row", "orders", "net_sales", "share_of_store_orders"]]
    for k, n in groups.items():
        out.append([k, n, money(rev[k]), pct(n, len(orders))])
    out.append(["Total", len(orders), money(sum(rev.values())), "100.0%"])
    return out


def one_row_per_order(orders: list[dict], column: str, blank_label: str) -> list[list]:
    counts: dict[str, int] = defaultdict(int)
    rev: dict[str, float] = defaultdict(float)
    for o in orders:
        key = o[column] or blank_label
        counts[key] += 1
        rev[key] += o["net_sales"]
    names = sorted((k for k in counts if k != blank_label), key=lambda k: -counts[k])
    if blank_label in counts:
        names.append(blank_label)
    out = [["row", "orders", "net_sales", "share_of_store_orders"]]
    for k in names:
        out.append([k, counts[k], money(rev[k]), pct(counts[k], len(orders))])
    total_n = sum(counts.values())
    total_rev = sum(rev.values())
    if total_n != len(orders):
        raise AssertionError("rows do not add up to the store total")
    out.append(["Total (matches Shopify)", total_n, money(total_rev), "100.0%"])
    return out


def claims_vs_mta(orders: list[dict]) -> list[list]:
    """Put each platform's own claim next to the orders the MTA placed on it."""
    out = [["platform", "orders_platform_claims", "orders_mta_places_on_it", "claimed_minus_mta"]]
    pairs = [
        ("Meta", lambda o: bool(o["meta_claim"]), lambda o: o["mta_channel"].lower().startswith("meta")),
        ("Google", lambda o: bool(o["google_claim"]), lambda o: o["mta_channel"].lower().startswith("google")),
    ]
    for name, claimed, placed in pairs:
        c = sum(1 for o in orders if claimed(o))
        m = sum(1 for o in orders if placed(o))
        out.append([name, c, m, c - m])
    return out


def daily_ratio(orders: list[dict], daily_path: str) -> list[list]:
    store = defaultdict(int)
    for o in orders:
        store[o["order_date"]] += 1
    platform: dict[str, dict[str, int]] = defaultdict(dict)
    with open(daily_path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            platform[r["source"]][r["date"]] = int(float(r["attributed_orders"] or 0))
    sources = sorted(platform)
    out = [["date", "shopify_orders"] + [f"{s}_orders" for s in sources] + [f"{s}_ratio" for s in sources]]
    for day in sorted(store):
        vals = [platform[s].get(day, 0) for s in sources]
        ratios = [f"{v / store[day]:.2f}" if store[day] else "" for v in vals]
        out.append([day, store[day]] + vals + ratios)
    return out


def write(table: list[list], path: Path) -> None:
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(table)


def show(title: str, table: list[list]) -> None:
    print(f"\n{title}")
    widths = [max(len(str(r[i])) for r in table) for i in range(len(table[0]))]
    for r in table:
        print("  " + "  ".join(str(c).ljust(w) for c, w in zip(r, widths)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orders", required=True)
    ap.add_argument("--daily")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    orders = load_orders(a.orders)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tables = [
        ("1_platform_claims.csv", "What each platform claims (these overlap)", platform_claims(orders)),
        ("2_overlap.csv", "Who claimed each order", overlap(orders)),
        ("3_ga4_rows.csv", "GA4, one row per order", one_row_per_order(orders, "ga4_channel", NOT_IN_GA4)),
        ("4_mta_rows.csv", "MTA, one row per order", one_row_per_order(orders, "mta_channel", UNATTRIBUTED)),
        ("5_claims_vs_mta.csv", "Platform claims next to MTA rows", claims_vs_mta(orders)),
    ]
    if a.daily:
        tables.append(("6_daily_ratio.csv", "Platform orders / Shopify orders, by day", daily_ratio(orders, a.daily)))
    for fname, title, t in tables:
        write(t, out / fname)
        show(title, t)
    print(f"\nWrote {len(tables)} files to {out}/")


if __name__ == "__main__":
    main()
