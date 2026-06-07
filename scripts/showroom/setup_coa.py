"""Apply / extend Chinese COA and tax configuration for the showroom company."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showroom._common import (
	account,
	bootstrap_path,
	cfg,
	commit,
	company,
	ensure_account,
	init_site,
	load_config,
	update_state,
)


def ensure_vat_accounts() -> dict[str, str]:
	"""Create 进项税额 / 销项税额 leaf accounts under 应交税费 (2221)."""
	import frappe
	parent_tax = account(account_number="2221", is_group=1)
	if not parent_tax:
		frappe.throw("Parent account 2221 应交税费 not found")

	input_vat = ensure_account(
		"22210101",
		"进项税额",
		"2221",
		"Liability",
		"Tax",
	)
	output_vat = ensure_account(
		"22210105",
		"销项税额",
		"2221",
		"Liability",
		"Tax",
	)
	return {"input_vat": input_vat, "output_vat": output_vat}


def ensure_production_accounts() -> None:
	"""Ensure doc-referenced production cost sub-accounts exist."""
	for number, name in (
		("50010101", "直接材料"),
		("50010102", "直接人工"),
		("50010103", "制造费用"),
	):
		if not account(account_number=number):
			ensure_account(number, name, "500101", "Expense", "Cost of Goods Sold")


def set_company_defaults() -> None:
	import frappe

	from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
		set_default_accounts,
	)

	comp = company()
	defaults = {
		"default_bank_account": account(account_number="1002"),
		"default_cash_account": account(account_number="1001"),
		"default_receivable_account": account(account_number="1122"),
		"default_payable_account": account(account_number="220201") or account(account_number="2202"),
		"default_inventory_account": account(account_number="1405"),
		"stock_received_but_not_billed": account(account_number="220202"),
		"default_income_account": account(account_number="6001"),
		"default_expense_account": account(account_number="6401") or account(account_number="5101"),
		"stock_adjustment_account": account(account_number="50010201"),
		"default_provisional_account": account(account_number="220202"),
	}
	# Run ERPNext defaults first, then re-apply doc-specific accounts so payable
	# stays on 220201 instead of the first generic Payable account (e.g. 2211).
	set_default_accounts(comp)
	defaults = {k: v for k, v in defaults.items() if v}
	frappe.db.set_value("Company", comp, defaults)


def ensure_tax_templates(vat_accounts: dict[str, str]) -> dict[str, str]:
	import frappe

	rate = cfg("vat_rate", 13)
	comp = company()
	result = {}

	sales_title = "增值税 13% 销项"
	if not frappe.db.exists("Sales Taxes and Charges Template", {"title": sales_title, "company": comp}):
		doc = frappe.get_doc(
			{
				"doctype": "Sales Taxes and Charges Template",
				"title": sales_title,
				"company": comp,
				"taxes": [
					{
						"charge_type": "On Net Total",
						"account_head": vat_accounts["output_vat"],
						"description": "销项税额 13%",
						"rate": rate,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
	result["sales_tax_template"] = sales_title

	purchase_title = "增值税 13% 进项"
	if not frappe.db.exists("Purchase Taxes and Charges Template", {"title": purchase_title, "company": comp}):
		doc = frappe.get_doc(
			{
				"doctype": "Purchase Taxes and Charges Template",
				"title": purchase_title,
				"company": comp,
				"taxes": [
					{
						"category": "Total",
						"add_deduct_tax": "Add",
						"charge_type": "On Net Total",
						"account_head": vat_accounts["input_vat"],
						"description": "进项税额 13%",
						"rate": rate,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
	result["purchase_tax_template"] = purchase_title

	item_tax_title = "VAT 13%"
	if not frappe.db.exists("Item Tax Template", item_tax_title):
		doc = frappe.get_doc(
			{
				"doctype": "Item Tax Template",
				"title": item_tax_title,
				"company": comp,
				"taxes": [
					{
						"tax_type": vat_accounts["output_vat"],
						"tax_rate": rate,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
	result["item_tax_template"] = item_tax_title

	return result


def setup_coa() -> dict:
	import frappe

	init_site()
	comp = company()

	if not frappe.db.exists("Company", comp):
		frappe.throw(f"Company not found: {comp}. Create it in Desk first or extend setup_company.")

	vat_accounts = ensure_vat_accounts()
	ensure_production_accounts()
	set_company_defaults()
	templates = ensure_tax_templates(vat_accounts)

	account_count = frappe.db.count("Account", {"company": comp})
	result = {
		"company": comp,
		"chart_of_accounts": cfg("chart_template"),
		"account_count": account_count,
		"vat_accounts": vat_accounts,
		"tax_templates": templates,
	}
	update_state(coa_setup=result)
	commit()
	return result


def run():
	bootstrap_path()
	load_config()
	result = setup_coa()
	print(result)
	return result


if __name__ == "__main__":
	run()
