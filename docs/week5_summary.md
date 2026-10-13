# Week 5 Summary

## What was done

This week focused on one question: are we holding the right amount of stock, too much, or too little? I reviewed turnover, stock health, aging, ABC classification, and overstock/understock risk using the cleaned inventory and sales data.

## Key findings

- Inventory turnover was calculated as units sold divided by average stock using a product-branch view. This shows which items move fast and which are sitting longer than expected.
- Stock health was classified using `current_stock` against `reorder_level`, `safety_stock`, and `max_stock`. The dataset contains a mix of healthy, low, critical, and overstocked product-branch pairs.
- Inventory aging was assessed using the last movement date instead of `running_balance`, because the balance values were found to be unreliable in the earlier validation work.
- ABC analysis shows that a relatively small share of products drives most of the revenue, consistent with a Pareto pattern.
- The biggest risk items are the product-branch pairs where current stock sits above the maximum or below the safety threshold, because these are the balances most likely to create extra holding cost or stockout exposure.
- The 9x stock-to-revenue finding depends on the revenue definition used. Relative to product-line revenue, stock value is roughly 8.7x; relative to order-level sales totals, it is about 1.0x. The difference matters because the project includes both line-level and order-level revenue values.

## Limitation

The stock ledger `running_balance` was not used for aging or stock health because earlier checks found it does not reconcile reliably for a meaningful share of movements. The analysis therefore relies on current stock and movement dates, which is more defensible for this phase.

## Files created

- notebooks/WEEK 5/week5_inventory_analytics.ipynb
- outputs/WEEK 5/week5_turnover_by_product_branch.csv
- outputs/WEEK 5/week5_turnover_by_branch.csv
- outputs/WEEK 5/week5_stock_health.csv
- outputs/WEEK 5/week5_inventory_aging.csv
- outputs/WEEK 5/week5_abc_classification.csv
- outputs/WEEK 5/week5_stock_risk.csv
- outputs/WEEK 5/week5_stock_value_vs_revenue.csv
- outputs/WEEK 5/week5_turnover_top_10.png
- outputs/WEEK 5/week5_stock_health_chart.png
- outputs/WEEK 5/week5_abc_pareto.png
- outputs/WEEK 5/week5_stock_risk_value.png
