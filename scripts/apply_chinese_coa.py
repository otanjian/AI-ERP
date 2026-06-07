#!/usr/bin/env python3
"""Apply Chinese Chart of Accounts (企业准则) to a company.

Reference: https://erpnext.cc/best-practice/财务实战/关于会计科目本地化/
"""
from __future__ import annotations

import frappe
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
	set_default_accounts,
	unset_existing_data,
)


CHART_TEMPLATE = "中国企业会计准则"
COMPANY = "博软科技 (Demo)"


def _cancel_submitted(doctype: str, company: str) -> int:
	count = 0
	for name in frappe.get_all(doctype, filters={"company": company, "docstatus": 1}, pluck="name"):
		doc = frappe.get_doc(doctype, name)
		doc.cancel()
		count += 1
	return count


def _delete_gl_entries(company: str) -> None:
	frappe.db.delete("GL Entry", {"company": company})
	frappe.db.delete("Payment Ledger Entry", {"company": company})


def apply_chinese_coa(company: str = COMPANY, chart_template: str = CHART_TEMPLATE) -> dict:
	frappe.only_for("System Manager")

	if not frappe.db.exists("Company", company):
		frappe.throw(f"Company not found: {company}")

	cancelled = {
		"Sales Invoice": _cancel_submitted("Sales Invoice", company),
		"Purchase Invoice": _cancel_submitted("Purchase Invoice", company),
		"Payment Entry": _cancel_submitted("Payment Entry", company),
	}
	_delete_gl_entries(company)

	unset_existing_data(company)

	frappe.db.set_value(
		"Company",
		company,
		{
			"chart_of_accounts": chart_template,
			"create_chart_of_accounts_based_on": "Standard Template",
		},
	)

	frappe.local.flags.ignore_root_company_validation = True
	create_charts(company, chart_template)

	set_default_accounts(company)

	# Prefer common Chinese manufacturing defaults over first-match heuristics.
	frappe.db.set_value(
		"Company",
		company,
		{
			"default_bank_account": _account(company, "1002"),
			"default_cash_account": _account(company, "1001"),
			"default_receivable_account": _account(company, "1122"),
			"default_payable_account": _account(company, "220201"),
			"default_inventory_account": _account(company, "1405"),
			"stock_received_but_not_billed": _account(company, "220202"),
			"default_income_account": _account(company, "6001"),
			"default_expense_account": _account(company, "5101"),
			"stock_adjustment_account": _account(company, "50010201"),
		},
	)

	account_count = frappe.db.count("Account", {"company": company})

	return {
		"company": company,
		"chart_of_accounts": chart_template,
		"cancelled_documents": cancelled,
		"account_count": account_count,
	}


def _account(company: str, account_number: str) -> str | None:
	return frappe.db.get_value("Account", {"company": company, "account_number": account_number})


def run():
	frappe.init(site="west.bosofts.com")
	frappe.connect()
	frappe.set_user("Administrator")
	result = apply_chinese_coa()
	frappe.db.commit()
	print(result)


if __name__ == "__main__":
	run()
