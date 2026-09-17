# Week 1 Profiling and Cleaning Report

This report records what I did during Week 1 of the Heavy Supplier, Inventory and Warehouse Analytics project. The aim was to look through the supplied files, check their quality, and prepare clean copies for the next stage.

## Files reviewed

I checked the 12 original CSV files in `data/raw`:

- `branches.csv`
- `customers.csv`
- `inventory_master.csv`
- `invoices.csv`
- `payments.csv`
- `products.csv`
- `purchase_orders_header.csv`
- `purchase_orders_lines.csv`
- `sales_orders_header.csv`
- `sales_orders_lines.csv`
- `stock_ledger.csv`
- `suppliers.csv`

The raw files were not edited. They remain the original source files for the project.

## Checks I completed

For each file, I checked:

- The number of rows and columns
- The column names
- The data types
- Missing values in each column
- Duplicate rows

## What I found

There were no duplicate rows. Most columns did not have missing values. The main missing-value finding was in `purchase_orders_header.csv`:

| File | Column | Missing values | Decision |
|---|---|---:|---|
| `purchase_orders_header.csv` | `received_date` | 2,370 | Kept blank because the related orders were returned and did not need a received date. |

I left these dates blank because the related orders were returned. A received date was not needed for those orders.

## What I changed

I converted the date fields from text to datetime values in these seven files:

- `customers.csv`: `customer_since`, `last_purchase_date`
- `invoices.csv`: `invoice_date`, `due_date`
- `payments.csv`: `payment_date`
- `products.csv`: `last_purchase_date`
- `purchase_orders_header.csv`: `order_date`, `expected_delivery_date`, `received_date`
- `sales_orders_header.csv`: `order_date`, `delivery_date`
- `stock_ledger.csv`: `movement_date`

I checked the data types after each conversion to make sure the changes worked.

The following five files did not need changes, so I copied them into the cleaned folder unchanged:

- `branches.csv`
- `inventory_master.csv`
- `purchase_orders_lines.csv`
- `sales_orders_lines.csv`
- `suppliers.csv`

## Saved files

The cleaned copies are saved in `data/cleaned`. There are 12 files in that folder. The original files in `data/raw` were not changed.
