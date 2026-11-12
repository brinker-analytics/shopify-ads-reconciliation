# Example data

Everything in this folder is made up. `scripts/make_example_data.py` generated it with a fixed seed, so you can rebuild the same files. It comes from no store, client or ad account.

- `EXAMPLE_orders.csv`: 380 example orders over 14 days in October 2026, one row per order.
- `EXAMPLE_platform_daily.csv`: example daily totals for Meta and Google Ads, the way you'd copy them out of each platform. The Meta rows include a few extra conversions per day that aren't flagged in the orders file, to stand in for modeled conversions.

The share of orders each platform touches, how often GA4 misses an order and how often the MTA can't place one are settings in the script. Real stores vary, so don't read the example output as a benchmark.
