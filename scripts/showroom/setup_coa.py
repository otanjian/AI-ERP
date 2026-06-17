"""Apply / extend Chinese COA and tax configuration for the showroom company."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showroom._common import (
	account,
	abbr,
	bootstrap_path,
	cfg,
	commit,
	company,
	ensure_account,
	init_site,
	load_config,
	update_state,
)

DOC_REQUIRED_ACCOUNTS = [
	("1122", "应收账款", "资产类", "Asset", "Receivable", 0),
	("1221", "其他应收款", "资产类", "Asset", "", 0),
	("1403", "原材料", "资产类", "Asset", "Stock", 0),
	("1408", "委托加工物资", "资产类", "Asset", "Stock", 0),
	("1405", "库存商品", "资产类", "Asset", "Stock", 0),
	("1602", "累计折旧", "资产类", "Asset", "Accumulated Depreciation", 0),
	("2202", "应付账款", "负债类", "Liability", "", 1),
	("220201", "应付账款-供应商款", "2202", "Liability", "Payable", 0),
	("220202", "应付账款-暂估", "2202", "Liability", "Stock Received But Not Billed", 0),
	("2221", "应交税费", "负债类", "Liability", "", 1),
	("222101", "应交增值税", "2221", "Liability", "", 1),
	("22210101", "进项税额", "222101", "Liability", "Tax", 0),
	("22210105", "销项税额", "222101", "Liability", "Tax", 0),
	("222112", "应交所得税", "2221", "Liability", "Tax", 0),
	("2211", "应付职工薪酬", "负债类", "Liability", "Payable", 0),
	("1002", "银行存款", "资产类", "Asset", "Bank", 0),
	("5001", "生产成本", "成本类", "Expense", "", 1),
	("500101", "直接材料", "5001", "Expense", "Cost of Goods Sold", 0),
	("500102", "直接人工", "5001", "Expense", "Cost of Goods Sold", 0),
	("500103", "制造费用", "5001", "Expense", "Cost of Goods Sold", 0),
	("6001", "主营业务收入", "损益类", "Income", "Income Account", 0),
	("6401", "主营业务成本", "损益类", "Income", "Expense Account", 0),
	("6602", "管理费用", "损益类", "Income", "Expense Account", 0),
	("6801", "所得税费用", "损益类", "Income", "Expense Account", 0),
	("4103", "本年利润", "权益类", "Equity", "Equity", 0),
]


def ensure_company() -> None:
	import frappe

	comp = company()
	if frappe.db.exists("Company", comp):
		frappe.db.set_value(
			"Company",
			comp,
			{
				"country": cfg("country", "China"),
				"default_currency": cfg("currency", "CNY"),
				"chart_of_accounts": cfg("chart_template"),
			},
		)
		return

	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": comp,
			"abbr": cfg("company_abbr"),
			"country": cfg("country", "China"),
			"default_currency": cfg("currency", "CNY"),
			"chart_of_accounts": cfg("chart_template"),
			"create_chart_of_accounts_based_on": "Standard Template",
		}
	)
	doc.insert(ignore_permissions=True)


def ensure_vat_accounts() -> dict[str, str]:
	"""Create 进项税额 / 销项税额 leaf accounts under 应交税费 (2221)."""
	ensure_account("222101", "应交增值税", "2221", "Liability", "", is_group=1)
	input_vat = ensure_account("22210101", "进项税额", "222101", "Liability", "Tax")
	output_vat = ensure_account("22210105", "销项税额", "222101", "Liability", "Tax")
	return {"input_vat": input_vat, "output_vat": output_vat}


def ensure_doc_accounts() -> dict[str, str]:
	import frappe

	for number in ("50010101", "50010102", "50010103", "50010104", "50010201", "50010202", "50010203"):
		name = account(account_number=number)
		if name and not frappe.db.exists("GL Entry", {"account": name}):
			frappe.delete_doc("Account", name, force=True, ignore_permissions=True)

	result = {}
	for number, name, parent, root_type, account_type, is_group in DOC_REQUIRED_ACCOUNTS:
		if parent in {"资产类", "负债类", "成本类", "损益类", "权益类"}:
			parent_account = frappe.db.get_value(
				"Account",
				{"company": company(), "account_name": parent, "parent_account": ["is", "not set"]},
				"name",
			)
			if not parent_account:
				frappe.throw(f"Root account not found: {parent}")
			parent_number = frappe.db.get_value("Account", parent_account, "account_number") or parent
			if parent_number == parent:
				# Root accounts in the Chinese chart do not have account numbers.
				existing = account(account_number=number)
				if existing:
					frappe.db.set_value(
						"Account",
						existing,
						{
							"account_name": name,
							"parent_account": parent_account,
							"root_type": root_type,
							"account_type": account_type or "",
							"is_group": is_group,
						},
					)
					result[number] = existing
					continue
				doc = frappe.get_doc(
					{
						"doctype": "Account",
						"account_name": name,
						"account_number": number,
						"parent_account": parent_account,
						"company": company(),
						"is_group": is_group,
						"root_type": root_type,
						"account_type": account_type or None,
					}
				)
				doc.insert(ignore_permissions=True)
				result[number] = doc.name
				continue
		result[number] = ensure_account(number, name, parent, root_type, account_type, is_group)
	return result


def set_company_defaults() -> None:
	import frappe

	from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
		set_default_accounts,
	)

	comp = company()
	stock_adjustment = account(account_number="500103") or account(account_number="6602")
	provisional = account(account_number="220202")
	if stock_adjustment or provisional:
		pre_defaults = {}
		if stock_adjustment:
			pre_defaults["stock_adjustment_account"] = stock_adjustment
		if provisional:
			pre_defaults["default_provisional_account"] = provisional
		frappe.db.set_value("Company", comp, pre_defaults)

	defaults = {
		"default_bank_account": account(account_number="1002"),
		"default_receivable_account": account(account_number="1122"),
		"default_payable_account": account(account_number="220201") or account(account_number="2202"),
		"default_inventory_account": account(account_number="1405"),
		"stock_received_but_not_billed": account(account_number="220202"),
		"default_income_account": account(account_number="6001"),
		"default_expense_account": account(account_number="6401"),
		"stock_adjustment_account": stock_adjustment,
		"default_provisional_account": account(account_number="220202"),
	}
	cash = account(account_number="1001")
	if cash:
		defaults["default_cash_account"] = cash
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
	existing_sales_tax = frappe.db.exists("Sales Taxes and Charges Template", {"title": sales_title, "company": comp})
	if not existing_sales_tax:
		doc = frappe.get_doc(
			{
				"doctype": "Sales Taxes and Charges Template",
				"title": sales_title,
				"company": comp,
				"is_default": 1,
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
		existing_sales_tax = doc.name
	frappe.db.set_value("Sales Taxes and Charges Template", {"company": comp}, "is_default", 0)
	frappe.db.set_value("Sales Taxes and Charges Template", existing_sales_tax, {"is_default": 1, "disabled": 0})
	result["sales_tax_template"] = sales_title

	purchase_title = "增值税 13% 进项"
	existing_purchase_tax = frappe.db.exists("Purchase Taxes and Charges Template", {"title": purchase_title, "company": comp})
	if not existing_purchase_tax:
		doc = frappe.get_doc(
			{
				"doctype": "Purchase Taxes and Charges Template",
				"title": purchase_title,
				"company": comp,
				"is_default": 1,
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
		existing_purchase_tax = doc.name
	frappe.db.set_value("Purchase Taxes and Charges Template", {"company": comp}, "is_default", 0)
	frappe.db.set_value("Purchase Taxes and Charges Template", existing_purchase_tax, {"is_default": 1, "disabled": 0})
	result["purchase_tax_template"] = purchase_title

	item_tax_title = "VAT 13%"
	existing_item_tax = frappe.db.exists(
		"Item Tax Template", {"title": item_tax_title, "company": comp}
	)
	if not existing_item_tax:
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
	ensure_company()
	comp = company()

	accounts = ensure_doc_accounts()
	vat_accounts = ensure_vat_accounts()
	set_company_defaults()
	templates = ensure_tax_templates(vat_accounts)

	account_count = frappe.db.count("Account", {"company": comp})
	result = {
		"company": comp,
		"chart_of_accounts": cfg("chart_template"),
		"account_count": account_count,
		"required_accounts": accounts,
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
