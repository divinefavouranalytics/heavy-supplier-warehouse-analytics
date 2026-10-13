# Week 4 Summary

## What was done

This week focused on product performance and demand. I reviewed revenue, units sold, and profit at product and category level, then checked which products are selling quickly versus those that are moving slowly or sitting with large stock balances.

## Key findings

- The highest revenue products are the engine, transmission, hydraulic, and undercarriage items. These products are the main drivers of sales and profit.
- Fast-moving products were defined as the top quartile by units sold. They are the items that should be protected from stockouts and replenished first.
- Slow-moving products were defined as the bottom quartile by units sold, with stock value tied up highlighted. These are the products most likely to be tying up cash in inventory.
- Under a strict rule of more than 365 days since the last OUT movement, no true dead-stock products were found. That means the major issue is not zero sales but overstocking and capital tied up in inventory.
- The monthly demand pattern shows clear product-level seasonality and category-level movement although the dataset is concentrated on a narrow set of high-volume items.

## Limitation

The stock ledger `running_balance` was not used for this analysis because the Week 3 validation found that it does not reconcile consistently. Instead, current stock and movement flows were used to assess performance and stock risk. This is a more reliable method for this phase.

## Files created

- notebooks/week4_product_analytics.ipynb
- outputs/week4_product_performance.csv
- outputs/week4_category_performance.csv
- outputs/week4_fast_moving_products.csv
- outputs/week4_slow_moving_products.csv
- outputs/week4_dead_stock_products.csv
- outputs/week4_monthly_product_demand.csv
- outputs/week4_monthly_category_demand.csv
- outputs/week4_top_products_revenue.png
- outputs/week4_category_revenue.png
- outputs/week4_fast_moving_chart.png
- outputs/week4_slow_moving_stock_value.png
- outputs/week4_monthly_category_demand.png
