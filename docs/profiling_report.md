# Profiling, Cleaning, Integration & Validation Report

This report records what was done in Weeks 1–3 of the Heavy Supplier, Inventory and Warehouse Analytics project. The aim was to look through the supplied files, check their quality, connect them together, and prepare the data for analysis.

---

## Week 1 — Profiling and Cleaning

### Files reviewed

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

### Checks I completed

For each file, I checked:

- The number of rows and columns
- The column names
- The data types
- Missing values in each column
- Duplicate rows
- Duplicate values in ID columns (checked separately from full duplicate rows, since an ID column being duplicated is a problem on its own even if the rest of the row differs)

### What I found

There were no fully duplicated rows in any file. Most columns did not have missing values. Three issues were found and fixed:

| File | Issue | Detail | Decision |
|---|---|---:|---|
| `purchase_orders_header.csv` | Missing `received_date` | 2,370 blanks | Kept blank — related orders were cancelled, so a received date does not apply. Not treated as an error. |
| `invoices.csv` | Duplicate `invoice_id` | 197 IDs reused across different invoices | Repeats relabelled with a suffix (e.g. `INV-361583-2`) so every ID is unique. |
| `payments.csv` | Duplicate `payment_id` | 202 IDs reused across different payments | Same fix as above. |
| `branches.csv` | `warehouse_capacity` stored as text | Values like `"45230 sqft"` | Split into a numeric `warehouse_capacity` column and a separate `warehouse_capacity_unit` column. |

### What I changed

I converted the date fields from text to datetime values in these seven files:

- `customers.csv`: `customer_since`, `last_purchase_date`
- `invoices.csv`: `invoice_date`, `due_date`
- `payments.csv`: `payment_date`
- `products.csv`: `last_purchase_date`
- `purchase_orders_header.csv`: `order_date`, `expected_delivery_date`, `received_date`
- `sales_orders_header.csv`: `order_date`, `delivery_date`
- `stock_ledger.csv`: `movement_date`

I checked the data types after each conversion to make sure the changes worked.

### Saved files

The cleaned copies are saved in `data/cleaned`. There are 12 files in that folder. The original files in `data/raw` were not changed.

---

## Week 2 — Integration and Feature Engineering

### Building the merged tables

I connected the cleaned files together into two combined tables:

- **`sales_table.csv`** — built by joining `sales_orders_lines` to `sales_orders_header` (on `so_id`), then adding `customers` (on `customer_id`), `branches` (on `branch_id`), and `invoices` (on `so_id`).
- **`purchases_fact_table.csv`** — built by joining `products` to `inventory_master` (on `product_id`), then adding `stock_ledger` (on `product_id` and `branch_id` together).

### Issues found while merging

| Issue | Detail | Fix |
|---|---|---|
| Payments merge caused row duplication | Merging `payments` directly onto the sales table using only `invoice_id` multiplied rows — an order with multiple product lines, matched against an invoice with multiple payments, produced more rows than it should (e.g. 3 lines × 3 payments = 9 rows instead of 3). | Summarised payments to one row per invoice first (`total_paid`, `number_of_payments`, `last_payment_date`), then merged that summary in instead of the raw payments table. |
| Stock ledger merge caused major row inflation | Merging `stock_ledger` using only `product_id` (without `branch_id`) matched every branch's stock movements to every branch's inventory row for that product, since a product exists at more than one branch. Incorrect result: 1,423,380 rows. Correct result: 237,230 rows. | Merged on `product_id` and `branch_id` together instead of `product_id` alone. |

After both fixes, `sales_table.csv` has 130,402 rows (matching `sales_orders_lines.csv`), and `purchases_fact_table.csv` has 237,230 rows (matching `stock_ledger.csv`).

### Feature engineering

New columns added to `sales_table.csv`:

- `delivery_lead_time_days` = `delivery_date` − `order_date`
- `profit_margin` = `unit_price` − `unit_cost` (in `purchases_fact_table.csv`)
- `days_to_pay_an_invoice` = `last_payment_date` − `invoice_date`

---

## Week 3 — Validation and First KPIs

### Validation checks completed

| Check | Result |
|---|---|
| Payments exceeding their invoice total | 308 processed invoices — total paid is more than the amount owed |
| Sales lines referencing a non-existent product | 0 — clean |
| Sales lines referencing a non-existent order | 0 — clean |
| Invoices referencing a non-existent order | 0 — clean |
| Orders referencing a non-existent customer | 0 — clean |
| Negative quantities, prices, or stock | 0 — clean |
| Orders delivered before they were placed | 0 — clean |
| Invoices dated before their order | 0 — clean |
| Payments dated before their invoice | 208 payments — flagged as a data entry issue |
| Stock ledger `running_balance` math errors | 32.93% of unambiguous IN/OUT movements don't match the expected calculation |

Relational integrity across the dataset is clean — every ID column correctly points to a real record in its parent table. The remaining issues are concentrated in payment amounts and stock ledger math, not in how the tables connect.

**Note on the stock ledger check:** `movement_id` is not a true sequence number. Product/branch/date groups with more than one movement on the same day were excluded because their exact order is unknown. The Week 3 notebook records the full reconciliation method and result.

### First KPIs

| KPI | Value |
|---|---|
| Total sales revenue | 32,424,754,555.80 |
| Total number of orders | 20,000 |
| Average order value | 1,621,237.73 |
| Outstanding payments | 5,835,028,760.19 across 5,586 invoices |
| Unique customers who've ordered | 500 |
| Total stock value (current inventory) | 281,292,677,410.00 |
| Average supplier lead time | 17.0 days |

**Early observation:** total stock value is roughly 9x total sales revenue, which is worth investigating further as a possible overstocking signal.

---

## Open issues for later phases

- 308 processed overpaid invoices — not yet investigated in depth.
- 208 payments with impossible dates — flagged, not deleted, since the payment amounts are likely still valid.
- 32.93% of unambiguous stock ledger movements have running_balance math that doesn't reconcile — worth deeper investigation, especially for later Stock Shrinkage Detection and Inventory Movement Anomaly Detection work.
