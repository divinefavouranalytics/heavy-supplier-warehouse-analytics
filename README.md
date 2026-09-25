# Heavy Supplier Warehouse Analytics

Supply-chain analytics project covering warehouse data profiling, cleaning, integration, feature engineering, and validation across 12 datasets for inventory and supplier analysis.

## Project Overview

This is my Phase 1 (Weeks 1-3) work for the Heavy Supplier, Inventory and Warehouse Analytics internship. I reviewed the supplied warehouse and supply-chain CSV files, checked their quality, cleaned and merged them, added new analytical columns, validated the results, and calculated first KPIs.

## Project Structure

- `data/raw/`: Original CSV files. Keep these files untouched.
- `data/cleaned/`: Cleaned and validated datasets.
- `notebooks/`: Week 1 profiling and cleaning notebooks.
- `docs/`: Data dictionary, profiling report, and supplied field documentation.
- `sql/`: SQL scripts for a later phase.
- `outputs/`: Charts, dashboards, exported tables, and Power BI-ready files.

## Week 1 Work Completed

- Reviewed all 12 files in `data/raw`.
- Checked row counts, columns, data types, missing values, duplicate rows, and duplicate ID values.
- Converted the date columns to datetime values.
- Fixed 197 duplicate `invoice_id` values and 202 duplicate `payment_id` values.
- Split `warehouse_capacity` in `branches.csv` into a numeric column and a unit column.
- Kept 2,370 blank `received_date` values because the related purchase orders were cancelled.
- Saved all 12 files in `data/cleaned`.

## Week 2 Work Completed

- Merged the cleaned files into two combined tables: `sales_table.csv` and `purchases_fact_table.csv`, saved in `data/processed`.
- Found and fixed a row-duplication bug caused by merging payments directly onto the sales table (fixed by summarising payments to one row per invoice first).
- Found and fixed a row-inflation bug in the purchases table caused by merging stock_ledger on `product_id` alone instead of `product_id` + `branch_id`.
- Added new feature columns: `delivery_lead_time_days`, `profit_margin`, and `days_to_pay_an_invoice`.

## Week 3 Work Completed

- Ran validation checks: payment amounts vs invoice totals, orphan record checks, negative value checks, and date logic checks.
- Found 308 processed invoices where total paid exceeds the invoice total.
- Found 208 payments dated before their invoice.
- Found that 32.93% of unambiguous stock ledger movements don't match the expected running balance math.
- Calculated first KPIs: total revenue, order count, average order value, outstanding payments, active customers, total stock value, and average supplier lead time.
- Updated the data dictionary and profiling report in `docs/` to cover Weeks 1-3.

## Current Status

- Week 1 profiling: Complete
- Week 1 cleaning: Complete
- Week 2 integration: Complete
- Week 2 feature engineering: Complete
- Week 3 validation: Complete
- Week 3 first KPIs: Complete
- Documentation: Complete (Weeks 1-3)
- SQL phase: Not started
- Power BI preparation: Not started
