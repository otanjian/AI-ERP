"""Company, warehouse, and item account defaults for the manufacturing showroom."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showroom._common import (
	account,
	bootstrap_path,
	commit,
	company,
	init_site,
	load_config,
	update_state,
	warehouse,
)

WAREHOUSE_ACCOUNTS = {
	"WH-RAW01": "1403",
	"WH-FG01": "1405",
	"WH-SUB01": "1408",
	"WH-WIP01": "500101",
}

PRODUCTION_EXPENSE = "500101"

RAW_ITEMS = {
	"ITEM-002",
	"ITEM-003",
	"ITEM-004",
	"ITEM-005",
	"ITEM-006",
	"ITEM-007",
	"ITEM-009",
	"ITEM-010",
}


def apply_company_account_defaults() -> dict[str, str]:
	import frappe

	comp = company()
	payable = account(account_number="220201") or account(account_number="2202")
	defaults = {
		"default_bank_account": account(account_number="1002"),
		"default_cash_account": account(account_number="1001"),
		"default_receivable_account": account(account_number="1122"),
		"default_payable_account": payable,
		"default_inventory_account": account(account_number="1405"),
		"stock_received_but_not_billed": account(account_number="220202"),
		"default_income_account": account(account_number="6001"),
		"default_expense_account": account(account_number="6401"),
		"stock_adjustment_account": account(account_number="500103") or account(account_number="6602"),
		"default_provisional_account": account(account_number="220202"),
	}
	defaults = {k: v for k, v in defaults.items() if v}
	frappe.db.set_value("Company", comp, defaults)
	return defaults


def apply_warehouse_accounts() -> dict[str, str]:
	import frappe

	result = {}
	for wh_code, acct_num in WAREHOUSE_ACCOUNTS.items():
		acct = account(account_number=acct_num)
		if not acct:
			continue
		wh_name = warehouse(wh_code)
		frappe.db.set_value("Warehouse", wh_name, "account", acct)
		result[wh_code] = acct
	return result


def _ensure_item_default(item_code: str, fields: dict) -> None:
	import frappe

	comp = company()
	existing = frappe.db.get_value("Item Default", {"parent": item_code, "company": comp}, "name")
	if existing:
		frappe.db.set_value("Item Default", existing, fields)
	else:
		doc = frappe.get_doc("Item", item_code)
		doc.append("item_defaults", {"company": comp, **fields})
		doc.save(ignore_permissions=True)


def apply_item_account_defaults() -> list[str]:
	import frappe

	updated = []
	wip_expense = account(account_number=PRODUCTION_EXPENSE)
	raw_inv = account(account_number="1403")
	fg_inv = account(account_number="1405")
	income = account(account_number="6001")
	cogs = account(account_number="6401")

	for code in RAW_ITEMS:
		_ensure_item_default(
			code,
			{
				"default_inventory_account": raw_inv,
				"expense_account": wip_expense,
				"default_warehouse": warehouse("WH-RAW01"),
			},
		)
		updated.append(code)

	_ensure_item_default(
		"ITEM-001",
		{
			"default_inventory_account": fg_inv,
			"income_account": income,
			"default_cogs_account": cogs,
			"expense_account": wip_expense,
			"default_warehouse": warehouse("WH-FG01"),
		},
	)
	updated.append("ITEM-001")

	_ensure_item_default(
		"ITEM-008",
		{
			"default_inventory_account": raw_inv,
			"expense_account": wip_expense,
			"default_warehouse": warehouse("WH-WIP01"),
		},
	)
	updated.append("ITEM-008")

	srv_expense = account(account_number="6401") or account(account_number="5101")
	if frappe.db.exists("Item", "SRV-SUB-001"):
		_ensure_item_default("SRV-SUB-001", {"expense_account": srv_expense})
		updated.append("SRV-SUB-001")

	return updated


def setup_account_defaults() -> dict:
	init_site()
	result = {
		"company": apply_company_account_defaults(),
		"warehouses": apply_warehouse_accounts(),
		"items": apply_item_account_defaults(),
	}
	update_state(account_defaults=result)
	commit()
	return result


def run():
	bootstrap_path()
	load_config()
	result = setup_account_defaults()
	print(result)
	return result


if __name__ == "__main__":
	run()
