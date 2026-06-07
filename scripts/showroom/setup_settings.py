"""Configure ERPNext module settings for manufacturing showroom."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showroom._common import account, bootstrap_path, commit, company, init_site, load_config, update_state


def setup_settings() -> dict:
	import frappe

	init_site()
	comp = company()

	stock = frappe.get_doc("Stock Settings")
	stock.enable_perpetual_inventory = 1
	stock.allow_negative_stock = 1
	wh = frappe.db.get_value("Warehouse", {"warehouse_name": "WH-RAW01", "company": comp})
	if wh:
		stock.default_warehouse = wh
	# Do not change valuation_method when stock transactions already exist.
	stock.save(ignore_permissions=True)

	buying = frappe.get_doc("Buying Settings")
	buying.maintain_same_rate = 1
	buying.allow_multiple_items = 1
	buying.save(ignore_permissions=True)

	selling = frappe.get_doc("Selling Settings")
	selling.allow_multiple_items = 1
	selling.save(ignore_permissions=True)

	mfg = frappe.get_doc("Manufacturing Settings")
	mfg.material_consumption = 1
	mfg.backflush_raw_materials_based_on = "BOM"
	mfg.overproduction_percentage_for_work_order = 0
	mfg.save(ignore_permissions=True)

	accounts = frappe.get_doc("Accounts Settings")
	accounts.auto_reconcile_payments = 1
	accounts.save(ignore_permissions=True)

	result = {
		"perpetual_inventory": stock.enable_perpetual_inventory,
		"valuation_method": stock.valuation_method,
	}
	update_state(settings_setup=result)
	commit()
	return result


def run():
	bootstrap_path()
	load_config()
	result = setup_settings()
	print(result)
	return result


if __name__ == "__main__":
	run()
