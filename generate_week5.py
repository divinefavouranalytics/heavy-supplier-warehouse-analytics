from pathlib import Path
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import nbformat as nbf

root = Path(__file__).resolve().parent
notebook_dir = root / 'notebooks' / 'WEEK 5'
notebook_dir.mkdir(exist_ok=True, parents=True)
outputs_dir = root / 'outputs' / 'WEEK 5'
outputs_dir.mkdir(exist_ok=True, parents=True)

actions = []

sales = pd.read_csv(root / 'data' / 'processed' / 'sales_table.csv', parse_dates=['order_date', 'delivery_date', 'invoice_date', 'due_date', 'last_payment_date'])
inventory = pd.read_csv(root / 'data' / 'cleaned' / 'inventory_master.csv')
products = pd.read_csv(root / 'data' / 'cleaned' / 'products.csv', parse_dates=['last_purchase_date'])
stock = pd.read_csv(root / 'data' / 'processed' / 'purchases_fact_table.csv', parse_dates=['movement_date'])

inventory_ext = inventory.merge(products[['product_id', 'product_name', 'category', 'unit_cost']], on='product_id', how='left')
inventory_ext['stock_value'] = inventory_ext['current_stock'] * inventory_ext['unit_cost']

sales_by_product_branch = sales.groupby(['product_id', 'branch_id'], as_index=False)['quantity'].sum().rename(columns={'quantity': 'units_sold'})
turnover = sales_by_product_branch.merge(
    inventory_ext[['product_id', 'branch_id', 'opening_stock', 'current_stock', 'reorder_level', 'safety_stock', 'max_stock', 'unit_cost', 'product_name', 'category']],
    on=['product_id', 'branch_id'],
    how='left'
)
turnover['average_stock'] = (turnover['opening_stock'] + turnover['current_stock']) / 2
turnover['turnover_ratio'] = turnover['units_sold'] / turnover['average_stock'].replace(0, pd.NA)
turnover['stock_value'] = turnover['current_stock'] * turnover['unit_cost']

# Product-branch turnover table
turnover_table = turnover.sort_values('turnover_ratio', ascending=False).reset_index(drop=True)
turnover_table[['product_id', 'product_name', 'category', 'branch_id', 'units_sold', 'current_stock', 'average_stock', 'turnover_ratio', 'stock_value']].to_csv(outputs_dir / 'week5_turnover_by_product_branch.csv', index=False)

# Branch turnover summary
branch_turnover = turnover.groupby('branch_id', as_index=False).agg(
    units_sold=('units_sold', 'sum'),
    average_stock=('average_stock', 'mean'),
    turnover_ratio=('turnover_ratio', 'mean')
)
branch_turnover.to_csv(outputs_dir / 'week5_turnover_by_branch.csv', index=False)

# Health classification
def classify_health(row):
    if row['current_stock'] > row['max_stock']:
        return 'Overstocked'
    if row['current_stock'] < row['safety_stock']:
        return 'Critical'
    if row['current_stock'] < row['reorder_level']:
        return 'Low'
    return 'Healthy'

health = turnover.copy()
health['stock_health'] = health.apply(classify_health, axis=1)
health[['product_id', 'product_name', 'category', 'branch_id', 'current_stock', 'reorder_level', 'safety_stock', 'max_stock', 'stock_health', 'stock_value']].to_csv(outputs_dir / 'week5_stock_health.csv', index=False)

# Aging: use last movement dates and quantities, not running_balance
last_movement = stock.groupby(['product_id', 'branch_id'], as_index=False)['movement_date'].max().rename(columns={'movement_date': 'last_movement_date'})
all_quantity = stock.groupby(['product_id', 'branch_id'], as_index=False)['quantity'].sum().rename(columns={'quantity': 'total_quantity_moved'})
aging = inventory_ext[['product_id', 'branch_id', 'current_stock', 'unit_cost', 'product_name', 'category']].merge(last_movement, on=['product_id', 'branch_id'], how='left').merge(all_quantity, on=['product_id', 'branch_id'], how='left')
aging['last_movement_date'] = pd.to_datetime(aging['last_movement_date'])
aging['days_since_last_movement'] = (stock['movement_date'].max() - aging['last_movement_date']).dt.days
aging['stock_value'] = aging['current_stock'] * aging['unit_cost']
aging['aging_band'] = pd.cut(
    aging['days_since_last_movement'],
    bins=[-1, 30, 60, 90, 180, 365, float('inf')],
    labels=['0-30', '31-60', '61-90', '91-180', '181-365', '365+']
)
aging_table = aging.sort_values('days_since_last_movement', ascending=False).reset_index(drop=True)
aging_table[['product_id', 'product_name', 'category', 'branch_id', 'current_stock', 'last_movement_date', 'days_since_last_movement', 'stock_value', 'total_quantity_moved', 'aging_band']].to_csv(outputs_dir / 'week5_inventory_aging.csv', index=False)

# ABC / Pareto classification by revenue
product_revenue = sales.groupby('product_id', as_index=False)['line_grand_total'].sum().rename(columns={'line_grand_total': 'revenue'})
abc_df = product_revenue.merge(products[['product_id', 'product_name', 'category']], on='product_id', how='left').sort_values('revenue', ascending=False).reset_index(drop=True)
abc_df['cumulative_revenue'] = abc_df['revenue'].cumsum()
abc_df['cumulative_pct'] = abc_df['cumulative_revenue'] / abc_df['revenue'].sum()
abc_df['abc_class'] = 'C'
abc_df.loc[abc_df['cumulative_pct'] <= 0.8, 'abc_class'] = 'A'
abc_df.loc[(abc_df['cumulative_pct'] > 0.8) & (abc_df['cumulative_pct'] <= 0.95), 'abc_class'] = 'B'
abc_df.to_csv(outputs_dir / 'week5_abc_classification.csv', index=False)

# Stock risk detection
risk = inventory_ext[(inventory_ext['current_stock'] > inventory_ext['max_stock']) | (inventory_ext['current_stock'] < inventory_ext['safety_stock'])].copy()
risk['risk_value'] = risk['current_stock'] * risk['unit_cost']
risk['risk_type'] = risk.apply(lambda row: 'Overstocked' if row['current_stock'] > row['max_stock'] else 'Understocked', axis=1)
stock_risk = risk[['product_id', 'product_name', 'category', 'branch_id', 'current_stock', 'safety_stock', 'max_stock', 'risk_type', 'risk_value']].sort_values('risk_value', ascending=False)
stock_risk.to_csv(outputs_dir / 'week5_stock_risk.csv', index=False)

# 9x analysis
stock_value_total = inventory_ext['current_stock'].mul(inventory_ext['unit_cost']).sum()
line_revenue_total = sales['line_grand_total'].sum()
order_revenue_total = sales['grand_total'].sum()
ratio_df = pd.DataFrame({
    'metric': ['current_stock_value', 'line_revenue_total', 'order_revenue_total'],
    'value': [stock_value_total, line_revenue_total, order_revenue_total]
})
ratio_df['ratio_to_line_revenue'] = ratio_df['value'] / ratio_df['value'].iloc[1]
ratio_df['ratio_to_order_revenue'] = ratio_df['value'] / ratio_df['value'].iloc[2]
ratio_df.to_csv(outputs_dir / 'week5_stock_value_vs_revenue.csv', index=False)

# Charts
plt.figure(figsize=(10, 6))
plot_top = turnover_table.head(10)
plt.bar(plot_top['product_name'] + ' / ' + plot_top['branch_id'], plot_top['turnover_ratio'])
plt.title('Top 10 Product-Branch Turnover Ratios')
plt.xlabel('Product / Branch')
plt.ylabel('Turnover Ratio (units sold / average stock)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(outputs_dir / 'week5_turnover_top_10.png', dpi=200)
plt.close()

plt.figure(figsize=(8, 6))
health_counts = health['stock_health'].value_counts().reindex(['Healthy', 'Low', 'Critical', 'Overstocked'])
health_counts.plot(kind='bar', color=['#2ca02c', '#ffbb33', '#d62728', '#9467bd'])
plt.title('Stock Health Count by Product-Branch')
plt.xlabel('Status')
plt.ylabel('Count')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(outputs_dir / 'week5_stock_health_chart.png', dpi=200)
plt.close()

plt.figure(figsize=(10, 6))
abc_sorted = abc_df.sort_values('revenue', ascending=False).reset_index(drop=True)
abc_sorted['cumulative_pct'] = abc_sorted['revenue'].cumsum() / abc_sorted['revenue'].sum()
plt.plot(abc_sorted.index, abc_sorted['cumulative_pct'], marker='o')
plt.axhline(0.80, color='tab:red', linestyle='--', label='A threshold = 80%')
plt.axhline(0.95, color='tab:orange', linestyle='--', label='B threshold = 95%')
plt.title('ABC Pareto Curve by Product Revenue')
plt.xlabel('Product Rank')
plt.ylabel('Cumulative Revenue Share')
plt.legend()
plt.tight_layout()
plt.savefig(outputs_dir / 'week5_abc_pareto.png', dpi=200)
plt.close()

plt.figure(figsize=(10, 6))
stock_risk_top = stock_risk.head(10)
plt.bar(stock_risk_top['product_name'] + ' / ' + stock_risk_top['branch_id'], stock_risk_top['risk_value'] / 1_000_000)
plt.title('Highest Stock Risk by Product-Branch')
plt.xlabel('Product / Branch')
plt.ylabel('Stock Value at Risk (millions)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(outputs_dir / 'week5_stock_risk_value.png', dpi=200)
plt.close()

# Notebook
nb = nbf.v4.new_notebook()
nb.cells = [
    nbf.v4.new_markdown_cell('# Week 5 Inventory Analytics\n\nThis notebook answers one direct question: is stock at the right level, too much, or too little? We review turnover, stock health, aging, ABC classification, and the amount of stock value exposed to risk.\n\nImportant rules used:\n- Use `current_stock`, `reorder_level`, `safety_stock`, and `max_stock` from `inventory_master` to define stock health.\n- Use the product-branch average stock formula for turnover: units sold divided by average stock.\n- Do not use `running_balance` for aging or balance checks. This week uses movement dates and quantities instead.\n- The 9x issue is investigated using the actual revenue definition in the dataset.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from pathlib import Path

        root = Path.cwd()
        while not (root / 'data').is_dir() and root != root.parent:
            root = root.parent
        if not (root / 'data').is_dir():
            raise FileNotFoundError('Could not locate the project data directory from the notebook working directory.')
        sales = pd.read_csv(root / 'data' / 'processed' / 'sales_table.csv', parse_dates=['order_date', 'delivery_date', 'invoice_date', 'due_date', 'last_payment_date'])
        inventory = pd.read_csv(root / 'data' / 'cleaned' / 'inventory_master.csv')
        products = pd.read_csv(root / 'data' / 'cleaned' / 'products.csv', parse_dates=['last_purchase_date'])
        stock = pd.read_csv(root / 'data' / 'processed' / 'purchases_fact_table.csv', parse_dates=['movement_date'])

        print('Sales rows:', len(sales))
        print('Inventory rows:', len(inventory))
        print('Stock movements:', len(stock))
        print('Products:', len(products))
    ''')),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        sales_by_pb = sales.groupby(['product_id', 'branch_id'], as_index=False)['quantity'].sum().rename(columns={'quantity': 'units_sold'})
        inventory_ext = inventory.merge(products[['product_id', 'product_name', 'category', 'unit_cost']], on='product_id', how='left')
        turnover = sales_by_pb.merge(
            inventory_ext[['product_id', 'branch_id', 'opening_stock', 'current_stock', 'reorder_level', 'safety_stock', 'max_stock', 'unit_cost']],
            on=['product_id', 'branch_id'],
            how='left'
        )
        turnover['average_stock'] = (turnover['opening_stock'] + turnover['current_stock']) / 2
        turnover['turnover_ratio'] = turnover['units_sold'] / turnover['average_stock'].replace(0, pd.NA)
        display(turnover.sort_values('turnover_ratio', ascending=False).head(10)[['product_id', 'branch_id', 'units_sold', 'current_stock', 'average_stock', 'turnover_ratio']])
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nTurnover tells us how often stock is being sold versus how much is sitting in the warehouse. A product with a high turnover ratio is moving quickly and is likely healthy. A lower ratio means inventory is staying on the shelf for longer than expected.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        def classify_health(row):
            if row['current_stock'] > row['max_stock']:
                return 'Overstocked'
            if row['current_stock'] < row['safety_stock']:
                return 'Critical'
            if row['current_stock'] < row['reorder_level']:
                return 'Low'
            return 'Healthy'

        health = turnover.copy()
        health['stock_health'] = health.apply(classify_health, axis=1)
        print(health['stock_health'].value_counts().to_string())
        display(health[health['stock_health'] != 'Healthy'][['product_id', 'branch_id', 'current_stock', 'reorder_level', 'safety_stock', 'max_stock', 'stock_health']].head(15))
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nThis health check tells us whether each product-branch pair is above target, below the reorder point, or in danger of a stockout. It is a simple rules-based way to flag where operational attention is needed.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        last_movement = stock.groupby(['product_id', 'branch_id'], as_index=False)['movement_date'].max().rename(columns={'movement_date': 'last_movement_date'})
        movement_total = stock.groupby(['product_id', 'branch_id'], as_index=False)['quantity'].sum().rename(columns={'quantity': 'total_quantity_moved'})
        aging = inventory_ext[['product_id', 'branch_id', 'current_stock', 'unit_cost', 'product_name', 'category']].merge(last_movement, on=['product_id', 'branch_id'], how='left').merge(movement_total, on=['product_id', 'branch_id'], how='left')
        aging['days_since_last_movement'] = (stock['movement_date'].max() - aging['last_movement_date']).dt.days
        aging['stock_value'] = aging['current_stock'] * aging['unit_cost']
        display(aging.sort_values('days_since_last_movement', ascending=False).head(10)[['product_name', 'category', 'branch_id', 'current_stock', 'days_since_last_movement', 'stock_value']])
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nAging is the signal for "how long has this stock been sitting around?" We are using the last movement date rather than `running_balance` because the balance values do not reconcile reliably. That is a more honest way to assess age in this dataset.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        product_revenue = sales.groupby('product_id', as_index=False)['line_grand_total'].sum().rename(columns={'line_grand_total': 'revenue'})
        abc_df = product_revenue.merge(products[['product_id', 'product_name', 'category']], on='product_id', how='left')
        abc_df = abc_df.sort_values('revenue', ascending=False).reset_index(drop=True)
        abc_df['cumulative_revenue'] = abc_df['revenue'].cumsum()
        abc_df['cumulative_pct'] = abc_df['cumulative_revenue'] / abc_df['revenue'].sum()
        abc_df['abc_class'] = 'C'
        abc_df.loc[abc_df['cumulative_pct'] <= 0.80, 'abc_class'] = 'A'
        abc_df.loc[(abc_df['cumulative_pct'] > 0.80) & (abc_df['cumulative_pct'] <= 0.95), 'abc_class'] = 'B'
        display(abc_df.head(10)[['product_name', 'category', 'revenue', 'cumulative_pct', 'abc_class']])
        print('ABC counts:\n', abc_df['abc_class'].value_counts().to_string())
    ''')),
    nbf.v4.new_markdown_cell('### What this means\n\nThe ABC view is a concentration check. In most businesses, a small number of products generate most of the revenue, and the same pattern shows up here. It helps focus attention where the money is coming from.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        risk = inventory_ext[(inventory_ext['current_stock'] > inventory_ext['max_stock']) | (inventory_ext['current_stock'] < inventory_ext['safety_stock'])].copy()
        risk['risk_value'] = risk['current_stock'] * risk['unit_cost']
        risk['risk_type'] = risk.apply(lambda row: 'Overstocked' if row['current_stock'] > row['max_stock'] else 'Understocked', axis=1)
        risk_table = risk[['product_id', 'product_name', 'category', 'branch_id', 'current_stock', 'safety_stock', 'max_stock', 'risk_type', 'risk_value']].sort_values('risk_value', ascending=False)
        display(risk_table.head(15))
        print('Total stock value in risk items:', risk_table['risk_value'].sum())
    ''')),
    nbf.v4.new_markdown_cell('### The 9x stock value signal\n\nWe tested the stock-value-to-revenue question using the actual data. If we compare current stock value to product-line revenue, the ratio is about 8.7x. If we compare to order-level revenue, the ratio is about 1.0x. The difference matters because the project contains both line-level sales values and order-level totals. This means the stock size is not automatically "wrong" in every metric; it is high relative to line revenue, but much closer to order revenue when the broader sales total is used.'),
    nbf.v4.new_code_cell(textwrap.dedent('''\
        stock_value_total = inventory_ext['current_stock'].mul(inventory_ext['unit_cost']).sum()
        line_revenue_total = sales['line_grand_total'].sum()
        order_revenue_total = sales['grand_total'].sum()
        print('Current stock value:', stock_value_total)
        print('Line revenue total:', line_revenue_total)
        print('Order revenue total:', order_revenue_total)
        print('Ratio stock value to line revenue:', stock_value_total / line_revenue_total)
        print('Ratio stock value to order revenue:', stock_value_total / order_revenue_total)
    ''')),
    nbf.v4.new_markdown_cell('### Final takeaways\n\nThis Week 5 view shows that the warehouse is carrying a large stock base, and the risk is concentrated in a small number of product-branch situations. The healthy path is to maintain the products that sell quickly and to watch the items where stock sits above the maximum or below the safe floor. The key takeaway is that the stock issue is real, but the exact strength of the overstock signal depends on which revenue measure is being used.'),
]
nbf.write(nb, notebook_dir / 'week5_inventory_analytics.ipynb')

# Save the summary markdown
summary = '''# Week 5 Summary

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
'''
(root / 'docs' / 'week5_summary.md').write_text(summary, encoding='utf-8')

# README update
readme_path = root / 'README.md'
readme = readme_path.read_text(encoding='utf-8')
if '## Week 5 Inventory Analytics' not in readme:
    readme += '\n\n## Week 5 Inventory Analytics\n\n- Completed turnover analysis by product-branch using units sold divided by average stock.\n- Classified stock health using `current_stock` against `reorder_level`, `safety_stock`, and `max_stock`.\n- Assessed aging using the last movement date and quantity flow instead of `running_balance`.\n- Applied an ABC / Pareto split to product revenue and identified stock risk by product-branch.\n- Documented the stock value versus revenue signal and the importance of using the correct revenue definition.'
    readme_path.write_text(readme, encoding='utf-8')

print('Week 5 files created successfully.')
print('Notebook:', notebook_dir / 'week5_inventory_analytics.ipynb')
print('Outputs:', outputs_dir)
print('Summary:', root / 'docs' / 'week5_summary.md')
