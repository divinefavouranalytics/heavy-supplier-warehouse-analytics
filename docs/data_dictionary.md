# Data Dictionary

This is a simple guide to the 12 files used in this project. It shows what each file is used for and the main ID fields in it.

## Table guide

| File | What it contains | Main IDs and links |
|---|---|---|
| `branches.csv` | Branch and warehouse details, capacity, employees, revenue, and operating costs. | `branch_id`, `manager_id` |
| `customers.csv` | Customer details, location, credit information, purchase history, and rating. | `customer_id`, `branch_id` |
| `inventory_master.csv` | Opening, reorder, safety, maximum, and current stock for products at each branch. | `product_id`, `branch_id` |
| `invoices.csv` | Invoice dates, order references, totals, and payment status. | `invoice_id`, `so_id`, `customer_id`, `branch_id` |
| `payments.csv` | Payments made against invoices, including dates, amounts, and methods. | `payment_id`, `invoice_id` |
| `products.csv` | Product descriptions, prices, costs, dimensions, weight, stock settings, and lead time. | `product_id` |
| `purchase_orders_header.csv` | Purchase order summary, supplier, branch, dates, status, and totals. | `po_id`, `supplier_id`, `branch_id` |
| `purchase_orders_lines.csv` | Individual products and quantities included in purchase orders. | `po_id`, `product_id`, `line_number` |
| `sales_orders_header.csv` | Sales order summary, customer, branch, dates, status, channel, and totals. | `so_id`, `customer_id`, `branch_id` |
| `sales_orders_lines.csv` | Individual products and quantities included in sales orders. | `so_id`, `product_id`, `line_number` |
| `stock_ledger.csv` | Stock movements, movement types, quantities, references, and running balances. | `movement_id`, `product_id`, `branch_id`, `reference_id` |
| `suppliers.csv` | Supplier details, product category, location, lead time, reliability, and duty rate. | `supplier_id` |

## Date fields cleaned in Week 1

I changed these date columns from text to datetime values in the cleaned files.

| File | Date fields |
|---|---|
| `customers.csv` | `customer_since`, `last_purchase_date` |
| `invoices.csv` | `invoice_date`, `due_date` |
| `payments.csv` | `payment_date` |
| `products.csv` | `last_purchase_date` |
| `purchase_orders_header.csv` | `order_date`, `expected_delivery_date`, `received_date` |
| `sales_orders_header.csv` | `order_date`, `delivery_date` |
| `stock_ledger.csv` | `movement_date` |

Note: CSV files can't store a real date type, so every time a cleaned file is loaded again, the date columns need to be converted back to datetime (`parse_dates=[...]`) — they read in as text otherwise.

## Other fields cleaned in Week 1

- `branches.csv` → `warehouse_capacity` was stored as text with the unit attached (e.g. `"45230 sqft"`). Split into a numeric `warehouse_capacity` column and a separate `warehouse_capacity_unit` column.
- `invoices.csv` → `invoice_id` had 197 duplicate values (the same ID used for two different invoices). Repeats were relabelled with a suffix (e.g. `INV-361583` → `INV-361583-2`) so every ID is unique.
- `payments.csv` → `payment_id` had 202 duplicate values, same issue and same fix as above.

## Other useful fields

- Sales and invoice values: `total_order_value`, `total_gst_amount`, `grand_total`
- Purchase order values: `total_cost`, `total_gst_amount`, `grand_total`
- Stock levels: `opening_stock`, `reorder_level`, `safety_stock`, `max_stock`, `current_stock`
- Product pricing: `unit_cost`, `unit_price`, `last_purchase_price`, `margin_percentage`
- Movement and order quantities: `quantity`
- Warehouse performance: `warehouse_capacity`, `total_employees`, `avg_monthly_revenue`, `monthly_operational_cost`
- Supplier performance: `lead_time_days`, `reliability_score`, `import_duty_rate`

## Missing-value note

`purchase_orders_header.csv` contains 2,370 blank values in `received_date`. These values were not filled because the related purchase orders were cancelled, so a received date was not required. The blanks were kept in the cleaned file to preserve the meaning of the original data.

## Merged tables (Week 2)

Two combined tables were built by joining the cleaned files together:

| File | What it contains | Built from |
|---|---|---|
| `sales_table.csv` | One row per product sold, with customer, branch, invoice, and payment details attached. | `sales_orders_lines` + `sales_orders_header` + `customers` + `branches` + `invoices` + a payments summary |
| `purchases_fact_table.csv` | One row per stock movement, with product, inventory, and purchasing details attached. | `products` + `inventory_master` + `stock_ledger` |

## New columns added (Week 2 — Feature Engineering)

| Column | In file | Calculation |
|---|---|---|
| `delivery_lead_time_days` | `sales_table.csv` | `delivery_date` − `order_date` |
| `profit_margin` | `purchases_fact_table.csv` | `unit_price` − `unit_cost` |
| `total_paid` | `sales_table.csv` | Sum of all payments for that invoice |
| `number_of_payments` | `sales_table.csv` | Count of payments for that invoice |
| `last_payment_date` | `sales_table.csv` | Most recent payment date for that invoice |
| `days_to_pay_an_invoice` | `sales_table.csv` | `last_payment_date` − `invoice_date` |

## Week 1–3 status

The cleaned versions of all 12 files are stored in `data/cleaned`. The original files in `data/raw` were left unchanged. The merged tables are stored in `data/processed`.
