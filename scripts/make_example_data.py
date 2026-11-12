"""Generate the EXAMPLE data in example_data/.

Every number this script writes is made up. It is seeded so the files are
reproducible. No store, client or platform account was used.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261111
OUT = Path(__file__).resolve().parent.parent / "example_data"

MTA_CHANNELS = ["Meta", "Google Search", "Google Shopping", "Email", "Organic search", "Direct", "Referral"]


def main() -> None:
    rng = random.Random(SEED)
    start = date(2026, 10, 5)
    rows = []
    n = 0
    for d in range(14):
        day = start + timedelta(days=d)
        for _ in range(rng.randint(22, 34)):
            n += 1
            net = round(rng.uniform(28, 140), 2)
            customer = "new" if rng.random() < 0.55 else "returning"
            # What the order "really" touched in this made-up world.
            touched_meta = rng.random() < 0.62
            touched_google = rng.random() < 0.5
            # Each platform can only claim orders connected to it.
            meta_claim = ""
            if touched_meta:
                meta_claim = "click" if rng.random() < 0.6 else "view"
            google_claim = "click" if touched_google and rng.random() < 0.85 else ""
            # GA4 misses some orders (blockers, consent, closed tabs).
            if rng.random() < 0.16:
                ga4 = ""
            elif touched_google and rng.random() < 0.6:
                ga4 = "Paid Search"
            elif meta_claim == "click" and rng.random() < 0.5:
                ga4 = "Paid Social"
            else:
                ga4 = rng.choice(["Direct", "Organic Search", "Email", "Referral", "Direct"])
            # The MTA places each order on one row, or leaves it unattributed.
            if rng.random() < 0.12:
                mta = ""
            elif meta_claim == "click" and rng.random() < 0.55:
                mta = "Meta"
            elif touched_google and rng.random() < 0.6:
                mta = rng.choice(["Google Search", "Google Shopping"])
            else:
                mta = rng.choice(MTA_CHANNELS[3:])
            rows.append({
                "order_id": f"EX-{1000 + n}",
                "order_date": day.isoformat(),
                "net_sales": f"{net:.2f}",
                "customer_type": customer,
                "meta_claim": meta_claim,
                "google_claim": google_claim,
                "ga4_channel": ga4,
                "mta_channel": mta,
            })
    OUT.mkdir(exist_ok=True)
    with open(OUT / "EXAMPLE_orders.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Daily platform totals, as you would copy them out of each ad platform.
    # Meta adds view-through and some conversions it models, so its daily
    # numbers can run above the orders flagged in EXAMPLE_orders.csv.
    daily = []
    for d in range(14):
        day = (start + timedelta(days=d)).isoformat()
        day_rows = [r for r in rows if r["order_date"] == day]
        meta = [r for r in day_rows if r["meta_claim"]]
        google = [r for r in day_rows if r["google_claim"]]
        extra = rng.randint(0, 3)
        daily.append({"date": day, "source": "Meta", "attributed_orders": len(meta) + extra,
                      "attributed_revenue": f"{sum(float(r['net_sales']) for r in meta) + extra * 70:.2f}"})
        daily.append({"date": day, "source": "Google Ads", "attributed_orders": len(google),
                      "attributed_revenue": f"{sum(float(r['net_sales']) for r in google):.2f}"})
    with open(OUT / "EXAMPLE_platform_daily.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(daily[0].keys()))
        w.writeheader()
        w.writerows(daily)


if __name__ == "__main__":
    main()
