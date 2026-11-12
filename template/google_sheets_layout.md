# Google Sheets layout

The same reconciliation as `reconcile.py`, built with formulas. Make a new sheet with four tabs.

## Tab 1: `Orders`

Paste one row per Shopify order, with these headers in row 1 (the same columns as `orders_template.csv`):

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| order_id | order_date | net_sales | customer_type | meta_claim | google_claim | ga4_channel | mta_channel |

- `meta_claim`: `click`, `view`, or blank. Fill it from the order IDs Meta reports, if you can get them, or from your MTA tool's platform view.
- `google_claim`: `click` or blank.
- `ga4_channel`: the GA4 session default channel group for the transaction. Leave it blank when GA4 has no record of the order.
- `mta_channel`: the single row your MTA places the order on. Leave it blank when the MTA can't place it.

Each order appears once. Check with `=COUNTA(Orders!A2:A)=COUNTUNIQUE(Orders!A2:A)`, which should say TRUE.

## Tab 2: `Claims`

| | A | B | C |
|---|---|---|---|
| 1 | row | orders | net_sales |
| 2 | Meta (click) | `=COUNTIF(Orders!E2:E,"click")` | `=SUMIF(Orders!E2:E,"click",Orders!C2:C)` |
| 3 | Meta (view) | `=COUNTIF(Orders!E2:E,"view")` | `=SUMIF(Orders!E2:E,"view",Orders!C2:C)` |
| 4 | Google Ads | `=COUNTIF(Orders!F2:F,"click")` | `=SUMIF(Orders!F2:F,"click",Orders!C2:C)` |
| 5 | Sum of platform claims | `=SUM(B2:B4)` | `=SUM(C2:C4)` |
| 6 | Shopify orders (store total) | `=COUNTA(Orders!A2:A)` | `=SUM(Orders!C2:C)` |
| 7 | Claims divided by store | `=B5/B6` | `=C5/C6` |

Row 5 can be bigger than row 6. When two platforms claim the same order, it is counted twice.

## Tab 3: `MTA rows`

| | A | B | C |
|---|---|---|---|
| 1 | row | orders | net_sales |
| 2 | `=SORT(UNIQUE(FILTER(Orders!H2:H,Orders!H2:H<>"")))` | `=COUNTIF(Orders!H$2:H,A2)` (fill down) | `=SUMIF(Orders!H$2:H,A2,Orders!C$2:C)` (fill down) |
| last+1 | Unattributed | `=COUNTIFS(Orders!A2:A,"<>",Orders!H2:H,"")` | `=SUMIFS(Orders!C2:C,Orders!A2:A,"<>",Orders!H2:H,"")` |
| last+2 | Total | `=SUM(B2:B_last+1)` | `=SUM(C2:C_last+1)` |
| last+3 | Matches Shopify? | `=B_total=Claims!B6` | |

The check cell must say TRUE. If it says FALSE, an order is missing or duplicated.

## Tab 4: `GA4 rows`

The same as Tab 3, using column G, with the blank row labeled `Not in GA4`.

## Optional tab: `Daily ratio`

Paste daily platform totals with the columns in `platform_daily_template.csv`. Next to each day, divide the platform's orders by that day's Shopify orders (`=COUNTIF(Orders!B2:B,A2)`). Watch the date the ratio changes, more than its level.
