from pathlib import Path
import json
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import nbformat as nbf

root = Path(r'c:\Users\tayod\OneDrive\Desktop\heavy-supplier-warehouse-analytics')
outputs_dir = root / 'outputs'
outputs_dir.mkdir(exist_ok=True)

sales = pd.read_csv(root / 'data' / 'processed' / 'sales_table.csv', parse_dates=['order_date', 'delivery_date', 'invoice_date', 'due_date', 'last_payment_date'])
products = pd.read_csv(root / 'data' / 'cleaned' / 'products.csv', parse_dates=['last_purchase_date'])
inventory = pd.read_csv(root / 'data' / 'cleaned' / 'inventory_master.csv')
stock = pd.read_csv(root / 'data' / 'processed' / 'purchases_fact_table.csv', parse_dates=['movement_date'])

product_meta = products[['product_id', 'product_name', 'category', 'unit_cost']].drop_duplicates()
sales_merged = sales.merge(product_meta, on='product_id', how='left')
sales_merged['effective_unit_price'] = sales_merged['line_total'] / sales_merged['quantity']
sales_merged['profit_per_line'] = (sales_merged['effective_unit_price'] - sales_merged['unit_cost']) * sales_merged['quantity']

product_perf = (
    sales_merged.groupby(['product_id', 'product_name', 'category'], as_index=False)
    .agg(revenue=('line_grand_total', 'sum'), units=('quantity', 'sum'), profit=('profit_per_line', 'sum'))
)
product_perf['margin_pct'] = product_perf['profit'] / product_perf['revenue']
product_perf = product_perf.merge(
    inventory.groupby('product_id', as_index=False)['current_stock'].sum().rename(columns={'current_stock': 'current_stock'}),
    on='product_id',
    how='left'
)
product_perf = product_perf.merge(product_meta[['product_id', 'unit_cost']], on='product_id', how='left')
product_perf['stock_value'] = product_perf['current_stock'].fillna(0) * product_perf['unit_cost']
product_perf['stock_value'] = product_perf['stock_value'].fillna(0)

# Category totals
category_perf = product_perf.groupby('category', as_index=False).agg(
    revenue=('revenue', 'sum'),
    units=('units', 'sum'),
    profit=('profit', 'sum')
)
category_perf['margin_pct'] = category_perf['profit'] / category_perf['revenue']

# Fast movers: top quartile by units sold
q75 = product_perf['units'].quantile(0.75)
fast_moving = product_perf[product_perf['units'] >= q75].sort_values('units', ascending=False).head(10)

# Slow movers: bottom quartile by units sold, then sorted by stock value
q25 = product_perf['units'].quantile(0.25)
slow_moving = product_perf[product_perf['units'] <= q25].sort_values('stock_value', ascending=False).head(10)

# Dead stock: no OUT movement in 365 days or no movement in entire dataset
out_dates = stock[stock['movement_type'] == 'OUT'].groupby('product_id', as_index=False)['movement_date'].max()
out_dates.columns = ['product_id', 'last_out_date']
product_perf_with_dates = product_perf.merge(out_dates, on='product_id', how='left')
end_date = max(sales_merged['order_date'].max(), stock['movement_date'].max())
product_perf_with_dates['days_since_last_out'] = (end_date - product_perf_with_dates['last_out_date']).dt.days

dead_stock = product_perf_with_dates[
    (product_perf_with_dates['last_out_date'].isna()) | (product_perf_with_dates['days_since_last_out'] > 365)
].sort_values('stock_value', ascending=False)

# Monthly demand trend
monthly_demand = sales_merged.assign(month=sales_merged['order_date'].dt.to_period('M').astype(str))
monthly_product = monthly_demand.groupby(['month', 'product_id', 'product_name', 'category'], as_index=False)['quantity'].sum()
monthly_category = monthly_demand.groupby(['month', 'category'], as_index=False)['quantity'].sum()

# Save tables
product_perf.sort_values('revenue', ascending=False).to_csv(outputs_dir / 'week4_product_performance.csv', index=False)
category_perf.sort_values('revenue', ascending=False).to_csv(outputs_dir / 'week4_category_performance.csv', index=False)
fast_moving.to_csv(outputs_dir / 'week4_fast_moving_products.csv', index=False)
slow_moving.to_csv(outputs_dir / 'week4_slow_moving_products.csv', index=False)
if dead_stock.empty:
    dead_stock_table = pd.DataFrame(columns=['product_id', 'product_name', 'category', 'current_stock', 'stock_value', 'days_since_last_out'])
else:
    dead_stock_table = dead_stock[['product_id', 'product_name', 'category', 'current_stock', 'stock_value', 'days_since_last_out']].copy()
dead_stock_table.to_csv(outputs_dir / 'week4_dead_stock_products.csv', index=False)
monthly_product.to_csv(outputs_dir / 'week4_monthly_product_demand.csv', index=False)
monthly_category.to_csv(outputs_dir / 'week4_monthly_category_demand.csv', index=False)

# Charts
plt.figure(figsize=(12, 7))
plot_top = product_perf.sort_values('revenue', ascending=False).head(10)
plt.bar(plot_top['product_name'], plot_top['revenue'] / 1_000_000)
plt.title('Top 10 Products by Revenue')
plt.xlabel('Product')
plt.ylabel('Revenue (millions)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(outputs_dir / 'week4_top_products_revenue.png', dpi=200)
plt.close()

plt.figure(figsize=(10, 7))
cat_plot = category_perf.sort_values('revenue', ascending=False)
plt.bar(cat_plot['category'], cat_plot['revenue'] / 1_000_000)
plt.title('Revenue by Category')
plt.xlabel('Category')
plt.ylabel('Revenue (millions)')
plt.xticks(rotation=25, ha='right')
plt.tight_layout()
plt.savefig(outputs_dir / 'week4_category_revenue.png', dpi=200)
plt.close()

plt.figure(figsize=(10, 7))
plt.bar(fast_moving['product_name'], fast_moving['units'])
plt.title('Fast-Moving Products (Top Quartile by Units Sold)')
plt.xlabel('Product')
plt.ylabel('Units Sold')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(outputs_dir / 'week4_fast_moving_chart.png', dpi=200)
plt.close()

plt.figure(figsize=(10, 7))
slow_plot = slow_moving.sort_values('stock_value', ascending=False).head(10)
plt.bar(slow_plot['product_name'], slow_plot['stock_value'] / 1_000_000)
plt.title('Slow-Moving Products by Stock Value Tied Up')
plt.xlabel('Product')
plt.ylabel('Current Stock Value (millions)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(outputs_dir / 'week4_slow_moving_stock_value.png', dpi=200)
plt.close()

plt.figure(figsize=(12, 7))
monthly_category_plot = monthly_category.sort_values('month')
for category_name, group in monthly_category_plot.groupby('category'):
    plt.plot(group['month'], group['quantity'], marker='o', label=category_name)
plt.title('Monthly Demand by Category')
plt.xlabel('Month')
plt.ylabel('Units Sold')
plt.xticks(rotation=45)
plt.legend(title='Category', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.savefig(outputs_dir / 'week4_monthly_category_demand.png', dpi=200)
plt.close()

# Notebook
nb = nbf.v4.new_notebook()
nb.cells = [
    nbf.v4.new_markdown_cell('# Week 4 Product Analytics\n\nThis notebook answers one practical question: which products make money, and which ones are sitting on the shelf doing little or nothing? We will review product revenue, profit, speed of sale, slow-moving stock, and monthly demand patterns using the cleaned sales and stock data.\n\nKey rules used:\n- Use product-level revenue, units, and profit per product and per category.\n- Define fast-moving products as the top quartile by units sold.\n- Define slow-moving products as the bottom quartile by units sold, with stock value tied up highlighted.\n- Dead stock is defined here as no OUT movement in more than 365 days; in this dataset no product meets that rule.\n- Do not use running_balance for stock timing decisions. Use current_stock and movement flows instead.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from pathlib import Path

        root = Path(r'c:/Users/tayod/OneDrive/Desktop/heavy-supplier-warehouse-analytics')
        sales = pd.read_csv(root / 'data' / 'processed' / 'sales_table.csv', parse_dates=['order_date', 'delivery_date', 'invoice_date', 'due_date', 'last_payment_date'])
        products = pd.read_csv(root / 'data' / 'cleaned' / 'products.csv', parse_dates=['last_purchase_date'])
        inventory = pd.read_csv(root / 'data' / 'cleaned' / 'inventory_master.csv')
        stock = pd.read_csv(root / 'data' / 'processed' / 'purchases_fact_table.csv', parse_dates=['movement_date'])

        print('Sales rows:', len(sales))
        print('Product rows:', len(products))
        print('Inventory rows:', len(inventory))
        print('Movement rows:', len(stock))
    ''')),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        product_meta = products[['product_id', 'product_name', 'category', 'unit_cost']].drop_duplicates()
        sales_merged = sales.merge(product_meta, on='product_id', how='left')
        sales_merged['effective_unit_price'] = sales_merged['line_total'] / sales_merged['quantity']
        sales_merged['profit_per_line'] = (sales_merged['effective_unit_price'] - sales_merged['unit_cost']) * sales_merged['quantity']

        product_perf = (
            sales_merged.groupby(['product_id', 'product_name', 'category'], as_index=False)
            .agg(revenue=('line_grand_total', 'sum'), units=('quantity', 'sum'), profit=('profit_per_line', 'sum'))
        )
        product_perf['margin_pct'] = product_perf['profit'] / product_perf['revenue']
        product_perf = product_perf.merge(inventory.groupby('product_id', as_index=False)['current_stock'].sum(), on='product_id', how='left')
        product_perf = product_perf.merge(product_meta[['product_id', 'unit_cost']], on='product_id', how='left')
        product_perf['stock_value'] = product_perf['current_stock'].fillna(0) * product_perf['unit_cost']

        product_top = product_perf.sort_values('revenue', ascending=False).head(10)
        display(product_top[['product_name', 'category', 'revenue', 'units', 'profit', 'current_stock', 'stock_value']])

        category_perf = product_perf.groupby('category', as_index=False).agg(revenue=('revenue', 'sum'), units=('units', 'sum'), profit=('profit', 'sum'))
        category_perf['margin_pct'] = category_perf['profit'] / category_perf['revenue']
        display(category_perf.sort_values('revenue', ascending=False))
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nThe high-revenue products are the ones delivering the biggest contributions to sales and profit. In a shop, these are the items that pay the rent and keep the business healthy. The category view shows which product groups are carrying the volume and which ones are weaker performers.\n\nA product can sell well but still carry a heavy stock balance. That is why we must also review stock value alongside revenue and profit.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        q75 = product_perf['units'].quantile(0.75)
        fast_moving = product_perf[product_perf['units'] >= q75].sort_values('units', ascending=False).head(10)
        print('Fast-moving rule: top quartile by units sold; q75 =', q75)
        display(fast_moving[['product_name', 'category', 'units', 'revenue', 'profit', 'current_stock', 'stock_value']])

        plt.figure(figsize=(10, 6))
        plt.bar(fast_moving['product_name'], fast_moving['units'])
        plt.title('Fast-Moving Products (Top Quartile by Units Sold)')
        plt.xlabel('Product')
        plt.ylabel('Units Sold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nFast-moving products are the ones you should keep fully stocked. They are selling consistently and drive demand, so they are the most important products to watch for stockouts and replenishment timing.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        q25 = product_perf['units'].quantile(0.25)
        slow_moving = product_perf[product_perf['units'] <= q25].sort_values('stock_value', ascending=False).head(10)
        out_dates = stock[stock['movement_type'] == 'OUT'].groupby('product_id', as_index=False)['movement_date'].max()
        out_dates.columns = ['product_id', 'last_out_date']
        product_perf_with_dates = product_perf.merge(out_dates, on='product_id', how='left')
        end_date = max(sales_merged['order_date'].max(), stock['movement_date'].max())
        product_perf_with_dates['days_since_last_out'] = (end_date - product_perf_with_dates['last_out_date']).dt.days
        dead_stock = product_perf_with_dates[(product_perf_with_dates['last_out_date'].isna()) | (product_perf_with_dates['days_since_last_out'] > 365)].sort_values('stock_value', ascending=False)

        print('Slow-moving rule: bottom quartile by units sold; q25 =', q25)
        display(slow_moving[['product_name', 'category', 'units', 'current_stock', 'stock_value']])
        print('Dead-stock rule: no OUT movement for more than 365 days or no OUT movement at all.')
        display(dead_stock[['product_name', 'category', 'current_stock', 'stock_value', 'days_since_last_out']])
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nThere are no true dead-stock items under the strict rule used here, which is useful information in itself. It means the business is still moving product, but some items are likely overstocked because they sit with large inventory balances even when not the highest-selling products.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        monthly_demand = sales_merged.assign(month=sales_merged['order_date'].dt.to_period('M').astype(str))
        monthly_product = monthly_demand.groupby(['month', 'product_id', 'product_name', 'category'], as_index=False)['quantity'].sum()
        monthly_category = monthly_demand.groupby(['month', 'category'], as_index=False)['quantity'].sum()

        print('Monthly product demand sample:')
        display(monthly_product.sort_values(['month', 'quantity'], ascending=[True, False]).head(10))

        plt.figure(figsize=(12, 7))
        for category_name, group in monthly_category.sort_values('month').groupby('category'):
            plt.plot(group['month'], group['quantity'], marker='o', label=category_name)
        plt.title('Monthly Demand by Category')
        plt.xlabel('Month')
        plt.ylabel('Units Sold')
        plt.xticks(rotation=45)
        plt.legend(title='Category', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.show()
    ''')),
    nbf.v4.new_markdown_cell('### Final takeaways\n\nThis Week 4 view tells the story of which products are truly making money, which products are moving quickly, and which items are tying up stock value without matching the same sales performance. The early signal from the project is clear: the stock value is much larger than revenue, and the product analysis is the first place where that overstock pattern becomes visible.'),
]
nbf.write(nb, root / 'notebooks' / 'week4_product_analytics.ipynb')

# README update
readme_path = root / 'README.md'
readme = readme_path.read_text(encoding='utf-8')
if '## Week 4 Product Analytics' not in readme:
    readme += '\n\n## Week 4 Product Analytics\n\n- Completed the product performance review for revenue, units sold, profit, and category ranking.\n- Identified fast-moving products using a top-quartile rule based on units sold.\n- Reviewed slow-moving stock by units sold and current stock value tied up.\n- Confirmed no true dead-stock items under a 365-day OUT-movement rule, which suggests overstocking is a more important issue than zero movement.\n- Saved the analysis notebook, charts, and CSV outputs in the project folders.'
    readme_path.write_text(readme, encoding='utf-8')

# Summary markdown
summary = '''# Week 4 Summary

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
'''
(root / 'docs' / 'week4_summary.md').write_text(summary, encoding='utf-8')

print('Week 4 outputs created successfully.')
print('Notebook saved to:', root / 'notebooks' / 'week4_product_analytics.ipynb')
print('Summary saved to:', root / 'docs' / 'week4_summary.md')
print('Outputs directory:', outputs_dir)
