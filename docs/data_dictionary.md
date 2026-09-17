# Week 1 Data Dictionary

This is a simple guide to the 12 files I reviewed during Week 1. It shows what each file is used for and the main ID fields in it.

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

### Dates

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

## Other useful fields

- Sales and invoice values: `total_order_value`, `total_gst_amount`, `grand_total`
- Purchase order values: `total_cost`, `total_gst_amount`, `grand_total`
- Stock levels: `opening_stock`, `reorder_level`, `safety_stock`, `max_stock`, `current_stock`
- Product pricing: `unit_cost`, `unit_price`, `last_purchase_price`, `margin_percentage`
- Movement and order quantities: `quantity`
- Warehouse performance: `warehouse_capacity`, `total_employees`, `avg_monthly_revenue`, `monthly_operational_cost`
- Supplier performance: `lead_time_days`, `reliability_score`, `import_duty_rate`

## Missing-value note

`purchase_orders_header.csv` contains 2,370 blank values in `received_date`. These values were not filled because the related purchase orders were returned, so a received date was not required. The blanks were kept in the cleaned file to preserve the meaning of the original data.

## Week 1 status

The cleaned versions of all 12 files are stored in `data/cleaned`. The original files in `data/raw` were left unchanged.
