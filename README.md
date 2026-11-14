# shopify-ads-reconciliation

Put your Shopify orders, what Meta and Google say they drove, what GA4 recorded and what your multi-touch attribution (MTA) tool assigned on one sheet, so you can see where they agree, where they overlap and which orders nobody can place.

> **Built by [Brinker Analytics](https://brinkeranalytics.com).** Eric Brinker's marketing-measurement practice for DTC brands.
> **Contact:** [eric@brinkeranalytics.com](mailto:eric@brinkeranalytics.com) or the [contact page](https://brinkeranalytics.com/contact).

## Why the numbers differ

Each ad platform counts the orders it can connect to its own ads: a click, and for Meta a view, inside its attribution window. It can't see the other platforms. When a buyer clicks a Meta ad, then a Google ad, then buys, both platforms count that order. Add up every platform's claims and the total can be larger than what the store sold.

Shopify counts each order once. GA4 records most orders but misses some (ad blockers, consent choices, buyers who close the tab before the confirmation page loads). An MTA tool tries to give each order one home.

This repo lays those views side by side. It doesn't decide which one is right, and it can't tell you whether an order would have happened without the ads. Attribution shows which ads were near a sale. To find out what happens without the ads, you have to test: turn the ads off for some people or places and compare.

## What you get

Six tables, each one a CSV:

| File | What it shows | Adds up to the store total? |
|---|---|---|
| `1_platform_claims.csv` | Orders each platform claims, next to Shopify's order count | No. Claims overlap. |
| `2_overlap.csv` | Orders claimed by Meta and Google, by one, or by neither | Yes |
| `3_ga4_rows.csv` | GA4 channels, plus a **Not in GA4** row | Yes |
| `4_mta_rows.csv` | MTA channels, plus an **Unattributed** row | Yes |
| `5_claims_vs_mta.csv` | Orders each platform claims next to the orders the MTA put on its row | No |
| `6_daily_ratio.csv` | Each platform's reported orders divided by Shopify orders, by day | No |

The rule behind tables 2 to 4: every Shopify order sits on exactly one row, and orders that can't be placed go on an Unattributed (or Not in GA4) row instead of being dropped. A good MTA places as many orders as it can. The Unattributed row tells you how many it couldn't.

The script stops with an error if an order ID appears twice, and checks that each one-row-per-order table adds up to the Shopify total.

## Run it on the example data

Python 3.9 or newer, standard library only.

```bash
python reconcile.py \
  --orders example_data/EXAMPLE_orders.csv \
  --daily example_data/EXAMPLE_platform_daily.csv \
  --out output
```

The example data is made up (see `example_data/README.md`). On it, the store has 380 orders. Meta and Google claim 404 between them, because 99 orders are claimed by both. Meta claims 246 orders; the MTA places 68 of them on Meta's row. The MTA leaves 55 orders unattributed, and GA4 has no record of 60. The committed results are in `example_output/`.

## Run it on your own data

1. Export your orders from Shopify for one date range. Use net sales, and keep test orders out.
2. Copy `template/orders_template.csv` and fill one row per order:
   - `meta_claim`: `click`, `view`, or blank, for orders Meta reports as its conversions. If you can't get order-level data from Meta, use your MTA tool's platform view, or skip this column and use the daily file.
   - `google_claim`: `click` or blank.
   - `ga4_channel`: the GA4 channel for the transaction ID, blank if GA4 has no record of it.
   - `mta_channel`: the one row your MTA tool places the order on, blank if it couldn't place it.
3. Optional: copy `template/platform_daily_template.csv` and fill in each platform's daily reported orders and revenue.
4. Run `reconcile.py` on your files.

Use the same date range, time zone and attribution setting in every source, or you'll be comparing different weeks.

Prefer a spreadsheet? `template/google_sheets_layout.md` builds the same tables with formulas. Have the data in a warehouse? `sql/reconcile_bigquery.sql` has the same queries in BigQuery SQL.

## Reading the results

- **Claims divided by store total.** Track it weekly. A sudden jump usually means something in the tracking changed on that date, such as a duplicated purchase event.
- **Not in GA4.** That share of orders is invisible in GA4 reports, whatever channel drove them.
- **Unattributed.** That share of orders has no channel in the MTA. Keep the row in every report so the totals still match Shopify.
- **Claimed minus MTA.** A big gap means the platform is counting orders that the MTA places on other channels.

None of these tables measure incrementality. They show what each system says happened, and they can't show what would have happened without the ads.

## What to do with this

- **If Meta and Google together claim more orders than Shopify sold,** stop adding platform ROAS together to judge total spend. Judge the total budget on store revenue divided by total ad spend, and use each platform's numbers to compare campaigns inside that platform.
- **If one platform claims far more orders than your MTA gives it,** that channel is a candidate for a test. Test it only if the answer might change the budget and you will act on the result. If both are true, hold its ads back in some regions and see whether sales there drop.
- **If the Unattributed or Not in GA4 rows are large,** fix the tracking before you move budget on any channel-level number.
- **If the claims ratio jumps on one day,** check what changed in the tracking on that date before you trust that week's ROAS.

If you want to know which of these numbers to trust with your budget, send me a note and we'll talk it through: [Schedule a call](https://brinkeranalytics.com/contact).

## Free reading on brinkeranalytics.com

- [Why your Meta, Google, GA4, Shopify, and finance numbers disagree](https://brinkeranalytics.com/insights/why-marketing-numbers-disagree)
- [When Meta, Google and others claim the same sales, which number decides spend?](https://brinkeranalytics.com/insights/when-platforms-claim-the-same-sales)
- [Should I trust Meta ROAS when purchase events are duplicated?](https://brinkeranalytics.com/insights/meta-roas-duplicate-purchase-events)
- [Why GA4 and Shopify revenue disagree](https://brinkeranalytics.com/insights/ga4-shopify-order-record)
- [Attribution models: what first-touch, last-touch, and multi-touch rules can tell you](https://brinkeranalytics.com/insights/attribution-models-explained)
- [Is my retargeting creating sales or just claiming them?](https://brinkeranalytics.com/insights/is-retargeting-creating-sales-or-claiming-them)
- [Custom multi-touch attribution for ecommerce starts with the order record](https://brinkeranalytics.com/multi-touch-attribution-ecommerce)
- [What is geo testing?](https://brinkeranalytics.com/insights/what-is-geo-testing): the next step when you want to know what happens without the ads
- [geo-test-pretest-checks](https://github.com/brinker-analytics/geo-test-pretest-checks): a companion repo with checks to run before a geo test

## Files

```
reconcile.py                      the script
template/orders_template.csv      blank orders file (one row per Shopify order)
template/platform_daily_template.csv  blank daily platform totals
template/google_sheets_layout.md  the same tables as spreadsheet formulas
sql/reconcile_bigquery.sql        the same tables in BigQuery SQL
example_data/                     made-up example data and how it was generated
example_output/                   results of the script on the example data
scripts/make_example_data.py      seeded generator for the example data
tests/test_reconcile.py           checks that rows add up to the store total
```

Run the tests with `python -m unittest discover -s tests`.

## License

The code is MIT licensed (see `LICENSE`). The documentation, including this README and the Google Sheets guide, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (see `LICENSE-docs`). If you reuse it, please credit Eric Brinker at [Brinker Analytics](https://www.brinkeranalytics.com).
