"""Shared helpers for showroom setup scripts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe
import yaml
from frappe.utils import flt, getdate, nowdate

SHOWROOM_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SHOWROOM_DIR / "fixtures"
BENCH_DIR = SHOWROOM_DIR.parent.parent


def bootstrap_path() -> None:
	import sys

	scripts_dir = str(SHOWROOM_DIR.parent)
	if scripts_dir not in sys.path:
		sys.path.insert(0, scripts_dir)


def load_config() -> dict[str, Any]:
	with open(SHOWROOM_DIR / "config.yaml", encoding="utf-8") as f:
		return yaml.safe_load(f)


def cfg(key: str, default: Any = None) -> Any:
	return load_config().get(key, default)


def company() -> str:
	return cfg("company")


def abbr() -> str:
	return cfg("company_abbr") or frappe.db.get_value("Company", company(), "abbr")


def posting_date(key: str | None = None) -> str:
	dates = cfg("posting_dates") or {}
	if key and key in dates:
		return dates[key]
	return str(nowdate())


def load_fixture(name: str) -> Any:
	path = FIXTURES_DIR / name
	with open(path, encoding="utf-8") as f:
		return json.load(f)


def state_path() -> Path:
	return SHOWROOM_DIR / cfg("state_file", "showroom_state.json")


def load_state() -> dict[str, Any]:
	path = state_path()
	if path.exists():
		with open(path, encoding="utf-8") as f:
			return json.load(f)
	return {}


def save_state(data: dict[str, Any]) -> None:
	path = state_path()
	with open(path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def update_state(**kwargs: Any) -> dict[str, Any]:
	state = load_state()
	state.update({k: v for k, v in kwargs.items() if v is not None})
	save_state(state)
	return state


def init_site(site: str | None = None) -> None:
	site = site or cfg("site")
	if not frappe.local.site:
		frappe.init(site=site, sites_path=str(BENCH_DIR / "sites"))
		frappe.connect()
	frappe.set_user("Administrator")
	frappe.flags.ignore_permissions = True


def account(account_number: str | None = None, account_name: str | None = None, is_group: int | None = None) -> str | None:
	filters: dict[str, Any] = {"company": company()}
	if is_group is not None:
		filters["is_group"] = is_group
	elif account_number is None:
		filters["is_group"] = 0
	if account_number:
		filters["account_number"] = account_number
	if account_name:
		filters["account_name"] = ["like", f"%{account_name}%"]
	return frappe.db.get_value("Account", filters, "name")


def warehouse(code: str) -> str:
	"""Resolve warehouse by warehouse_name code (e.g. WH-RAW01)."""
	comp = company()
	name = frappe.db.get_value("Warehouse", {"warehouse_name": code, "company": comp})
	if name:
		return name
	# fallback suffix pattern
	candidates = frappe.get_all(
		"Warehouse",
		filters={"company": comp, "warehouse_name": ["like", f"%{code}%"]},
		pluck="name",
	)
	if candidates:
		return candidates[0]
	frappe.throw(f"Warehouse not found for code: {code}")


def item_code(code: str) -> str:
	if frappe.db.exists("Item", code):
		return code
	frappe.throw(f"Item not found: {code}")


def ensure_account(
	account_number: str,
	account_name: str,
	parent_number: str,
	root_type: str,
	account_type: str = "",
) -> str:
	existing = account(account_number=account_number)
	if existing:
		return existing

	parent = frappe.db.get_value(
		"Account", {"company": company(), "account_number": parent_number}, "name"
	)
	if not parent:
		frappe.throw(f"Parent account {parent_number} not found for {account_name}")

	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": account_name,
			"account_number": account_number,
			"parent_account": parent,
			"company": company(),
			"is_group": 0,
			"root_type": root_type,
			"account_type": account_type or None,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_warehouse(data: dict[str, Any]) -> str:
	comp = company()
	wh_name = data["warehouse_name"]
	existing = frappe.db.get_value("Warehouse", {"warehouse_name": wh_name, "company": comp})
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": wh_name,
			"company": comp,
			"is_group": 0,
			"parent_warehouse": data.get("parent_warehouse"),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_item(data: dict[str, Any], accounts: dict[str, str | None]) -> str:
	code = data["item_code"]
	if frappe.db.exists("Item", code):
		return code

	doc = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": code,
			"item_name": data["item_name"],
			"item_group": data["item_group"],
			"stock_uom": data["stock_uom"],
			"is_stock_item": 1,
			"include_item_in_manufacturing": data.get("include_item_in_manufacturing", 1),
			"is_purchase_item": data.get("is_purchase_item", 1),
			"is_sales_item": data.get("is_sales_item", 0),
			"is_sub_contracted_item": data.get("is_sub_contracted_item", 0),
			"valuation_method": data.get("valuation_method", "Moving Average"),
			"default_warehouse": warehouse(data["default_warehouse"]) if data.get("default_warehouse") else None,
			"standard_rate": data.get("standard_rate", 0),
		}
	)
	group_key = data.get("item_group")
	if group_key in accounts and accounts[group_key]:
		for field in ("expense_account", "income_account"):
			pass
	doc.insert(ignore_permissions=True)
	return code


def get_bin_qty(item: str, wh_code: str) -> float:
	wh = warehouse(wh_code)
	return flt(
		frappe.db.get_value("Bin", {"item_code": item, "warehouse": wh}, "actual_qty")
	)


def gl_balance(acct_number: str) -> float:
	acct = account(account_number=acct_number)
	if not acct:
		return 0.0
	debit = frappe.db.sql(
		"""SELECT COALESCE(SUM(debit), 0) FROM `tabGL Entry`
		WHERE account = %s AND company = %s AND is_cancelled = 0""",
		(acct, company()),
	)[0][0]
	credit = frappe.db.sql(
		"""SELECT COALESCE(SUM(credit), 0) FROM `tabGL Entry`
		WHERE account = %s AND company = %s AND is_cancelled = 0""",
		(acct, company()),
	)[0][0]
	return flt(debit - credit)


def commit() -> None:
	frappe.db.commit()
