"""Load showroom master data from JSON fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showroom._common import (
	account,
	bootstrap_path,
	commit,
	company,
	ensure_warehouse,
	init_site,
	load_fixture,
	posting_date,
	update_state,
	warehouse,
)


def setup_item_groups() -> list[str]:
	import frappe

	created = []
	for row in load_fixture("item_groups.json"):
		name = row["item_group_name"]
		if frappe.db.exists("Item Group", name):
			frappe.db.set_value("Item Group", name, "item_group_name", name)
			created.append(name)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": name,
				"parent_item_group": row.get("parent_item_group", "All Item Groups"),
				"is_group": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(name)
	return created


def setup_warehouses() -> list[str]:
	return [ensure_warehouse(row) for row in load_fixture("warehouses.json")]


def setup_items() -> list[str]:
	import frappe

	created = []
	for row in load_fixture("items.json"):
		code = row["item_code"]
		if frappe.db.exists("Item", code):
			updates = {
				"item_name": row["item_name"],
				"item_group": row["item_group"],
				"stock_uom": row["stock_uom"],
				"include_item_in_manufacturing": row.get("include_item_in_manufacturing", 1),
				"is_purchase_item": row.get("is_purchase_item", 1),
				"is_sales_item": row.get("is_sales_item", 0),
				"is_sub_contracted_item": row.get("is_sub_contracted_item", 0),
				"valuation_method": row.get("valuation_method", "Moving Average"),
				"standard_rate": row.get("standard_rate", 0),
			}
			if row.get("is_stock_item") == 0:
				updates["is_stock_item"] = 0
			if row.get("default_warehouse"):
				updates["default_warehouse"] = warehouse(row["default_warehouse"])
			frappe.db.set_value("Item", code, updates)
			created.append(code)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": row["item_name"],
				"item_group": row["item_group"],
				"stock_uom": row["stock_uom"],
				"is_stock_item": 1,
				"include_item_in_manufacturing": row.get("include_item_in_manufacturing", 1),
				"is_purchase_item": row.get("is_purchase_item", 1),
				"is_sales_item": row.get("is_sales_item", 0),
				"is_sub_contracted_item": row.get("is_sub_contracted_item", 0),
				"valuation_method": row.get("valuation_method", "Moving Average"),
				"standard_rate": row.get("standard_rate", 0),
			}
		)
		if row.get("default_warehouse"):
			doc.default_warehouse = warehouse(row["default_warehouse"])
		doc.insert(ignore_permissions=True)
		created.append(code)
	return created


def setup_boms() -> list[str]:
	import frappe

	created = []
	for row in load_fixture("boms.json"):
		item_code = row["item"]
		existing = frappe.db.get_value("BOM", {"item": item_code, "is_active": 1, "docstatus": 1}, "name")
		if existing:
			frappe.db.set_value("Item", item_code, "default_bom", existing)
			created.append(existing)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": item_code,
				"quantity": row.get("quantity", 1),
				"company": company(),
				"is_active": 1,
				"is_default": 1,
				"with_operations": 0,
				"items": [
					{
						"item_code": line["item_code"],
						"qty": line["qty"],
						"uom": frappe.db.get_value("Item", line["item_code"], "stock_uom"),
					}
					for line in row["items"]
				],
			}
		)
		if row.get("is_subcontracted"):
			doc.is_subcontracted = 1
		doc.insert(ignore_permissions=True)
		doc.submit()
		frappe.db.set_value("Item", item_code, "default_bom", doc.name)
		created.append(doc.name)
	return created


def setup_subcontracting_bom() -> str | None:
	import frappe

	if frappe.db.exists("Subcontracting BOM", {"finished_good": "ITEM-008", "is_active": 1}):
		return frappe.db.get_value("Subcontracting BOM", {"finished_good": "ITEM-008", "is_active": 1})

	if not frappe.db.exists("Item", "SRV-SUB-001"):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "SRV-SUB-001",
				"item_name": "散热模组委外加工费",
				"item_group": "GRP-004",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_purchase_item": 1,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("Item", "SRV-SUB-001", {"is_stock_item": 0, "is_purchase_item": 1})

	fg_bom = frappe.db.get_value("Item", "ITEM-008", "default_bom")
	doc = frappe.get_doc(
		{
			"doctype": "Subcontracting BOM",
			"is_active": 1,
			"finished_good": "ITEM-008",
			"finished_good_qty": 1,
			"finished_good_bom": fg_bom,
			"service_item": "SRV-SUB-001",
			"service_item_qty": 1,
			"conversion_factor": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def setup_parties() -> dict[str, list[str]]:
	import frappe

	data = load_fixture("parties.json")
	result: dict[str, list[str]] = {"customers": [], "suppliers": []}

	for row in data.get("customers", []):
		name = row["name"]
		if not frappe.db.exists("Customer", name):
			doc = frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": row["customer_name"],
					"customer_type": row.get("customer_type", "Company"),
					"customer_group": "Commercial",
					"territory": "All Territories",
				}
			)
			doc.insert(ignore_permissions=True)
			if doc.name != name:
				frappe.rename_doc("Customer", doc.name, name, force=True)
		else:
			frappe.db.set_value("Customer", name, "customer_name", row["customer_name"])
		if row.get("credit_limit"):
			company_credit_limit = frappe.db.get_value(
				"Customer Credit Limit",
				{"parent": name, "company": company()},
				"name",
			)
			if company_credit_limit:
				frappe.db.set_value("Customer Credit Limit", company_credit_limit, "credit_limit", row["credit_limit"])
			else:
				doc = frappe.get_doc("Customer", name)
				doc.append("credit_limits", {"company": company(), "credit_limit": row["credit_limit"]})
				doc.save(ignore_permissions=True)
		result["customers"].append(name)

	for row in data.get("suppliers", []):
		name = row["name"]
		if not frappe.db.exists("Supplier", name):
			doc = frappe.get_doc(
				{
					"doctype": "Supplier",
					"supplier_name": row["supplier_name"],
					"supplier_type": row.get("supplier_type", "Company"),
					"supplier_group": row.get("supplier_group", "All Supplier Groups"),
				}
			)
			doc.insert(ignore_permissions=True)
			if doc.name != name:
				frappe.rename_doc("Supplier", doc.name, name, force=True)
		else:
			frappe.db.set_value("Supplier", name, "supplier_name", row["supplier_name"])
		result["suppliers"].append(name)

	return result


def setup_opening_stock() -> str | None:
	import frappe

	rows = load_fixture("opening_stock.json")
	comp = company()
	existing = frappe.db.get_value(
		"Stock Reconciliation",
		{"company": comp, "purpose": "Opening Stock", "docstatus": 1},
		"name",
	)
	if existing:
		return existing

	items = []
	for row in rows:
		items.append(
			{
				"item_code": row["item_code"],
				"warehouse": warehouse(row["warehouse"]),
				"qty": row["qty"],
				"valuation_rate": row["valuation_rate"],
			}
		)

	from showroom._common import account

	opening_equity = account(account_number="4002") or account(account_number="4001")
	cost_center = frappe.db.get_value("Cost Center", {"company": comp, "is_group": 0}, "name")

	doc = frappe.get_doc(
		{
			"doctype": "Stock Reconciliation",
			"company": comp,
			"purpose": "Opening Stock",
			"posting_date": posting_date("sales_order"),
			"posting_time": "09:00:00",
			"set_posting_time": 1,
			"expense_account": opening_equity,
			"cost_center": cost_center,
			"items": items,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def setup_masters() -> dict:
	init_site()
	from showroom.account_defaults import setup_account_defaults

	result = {
		"item_groups": setup_item_groups(),
		"warehouses": setup_warehouses(),
		"items": setup_items(),
		"boms": setup_boms(),
		"subcontracting_bom": setup_subcontracting_bom(),
		"parties": setup_parties(),
		"opening_stock": setup_opening_stock(),
	}
	account_defaults = setup_account_defaults()
	result["account_defaults"] = account_defaults
	update_state(masters_setup=result)
	commit()
	return result


def run():
	bootstrap_path()
	result = setup_masters()
	print(result)
	return result


if __name__ == "__main__":
	run()
