"""Execute showroom business flow per doc/10 样板间（制造行业）.md."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import frappe

from showroom._common import (
	bootstrap_path,
	cfg,
	commit,
	company,
	init_site,
	load_state,
	posting_date,
	update_state,
	warehouse,
)


def _tax_template(doctype: str, title: str) -> str | None:
	return frappe.db.get_value(doctype, {"title": title, "company": company()})


def _supplier_name(supplier: str) -> str:
	return frappe.db.get_value("Supplier", supplier, "supplier_name") or supplier


def _get_or_create_sales_order(state: dict) -> str:
	if state.get("sales_order") and frappe.db.exists("Sales Order", state["sales_order"]):
		return state["sales_order"]

	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"company": company(),
			"customer": "CUST-001",
			"transaction_date": posting_date("sales_order"),
			"delivery_date": posting_date("delivery"),
			"items": [
				{
					"item_code": "ITEM-001",
					"qty": 50,
					"rate": 3500,
					"delivery_date": posting_date("delivery"),
					"warehouse": warehouse("WH-FG01"),
				}
			],
		}
	)
	tmpl = _tax_template("Sales Taxes and Charges Template", "增值税 13% 销项")
	if tmpl:
		so.taxes_and_charges = tmpl
	so.insert(ignore_permissions=True)
	so.submit()
	update_state(sales_order=so.name)
	return so.name


def _create_material_request(state: dict) -> str:
	if state.get("material_request") and frappe.db.exists("Material Request", state["material_request"]):
		return state["material_request"]

	lines = [
		("ITEM-002", 40),
		("ITEM-003", 35),
		("ITEM-004", 70),
		("ITEM-005", 30),
		("ITEM-006", 25),
		("ITEM-007", 10),
		("ITEM-008", 50),
	]
	mr = frappe.get_doc(
		{
			"doctype": "Material Request",
			"company": company(),
			"material_request_type": "Purchase",
			"transaction_date": posting_date("mrp"),
			"schedule_date": posting_date("po_receipt"),
			"items": [
				{
					"item_code": item,
					"qty": qty,
					"schedule_date": posting_date("po_receipt"),
					"warehouse": warehouse("WH-RAW01"),
				}
				for item, qty in lines
			],
		}
	)
	mr.insert(ignore_permissions=True)
	mr.submit()
	update_state(material_request=mr.name)
	return mr.name


def _create_po_supp1(state: dict) -> str:
	key = "po_supp1"
	if state.get(key) and frappe.db.exists("Purchase Order", state[key]):
		return state[key]

	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"company": company(),
			"supplier": "SUPP-001",
			"supplier_name": _supplier_name("SUPP-001"),
			"transaction_date": posting_date("po_supp1"),
			"schedule_date": posting_date("po_receipt"),
			"items": [
				{
					"item_code": "ITEM-002",
					"qty": 40,
					"rate": 1200,
					"schedule_date": posting_date("po_receipt"),
					"warehouse": warehouse("WH-RAW01"),
				},
				{
					"item_code": "ITEM-003",
					"qty": 35,
					"rate": 800,
					"schedule_date": posting_date("po_receipt"),
					"warehouse": warehouse("WH-RAW01"),
				},
			],
		}
	)
	tmpl = _tax_template("Purchase Taxes and Charges Template", "增值税 13% 进项")
	if tmpl:
		po.taxes_and_charges = tmpl
	po.insert(ignore_permissions=True)
	po.submit()
	update_state(**{key: po.name})
	return po.name


def _create_po_supp2(state: dict) -> str:
	key = "po_supp2"
	if state.get(key) and frappe.db.exists("Purchase Order", state[key]):
		return state[key]

	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"company": company(),
			"supplier": "SUPP-002",
			"supplier_name": _supplier_name("SUPP-002"),
			"transaction_date": posting_date("po_supp1"),
			"schedule_date": posting_date("po_receipt"),
			"items": [
				{"item_code": "ITEM-004", "qty": 70, "rate": 200, "warehouse": warehouse("WH-RAW01")},
				{"item_code": "ITEM-005", "qty": 30, "rate": 350, "warehouse": warehouse("WH-RAW01")},
				{"item_code": "ITEM-006", "qty": 25, "rate": 150, "warehouse": warehouse("WH-RAW01")},
				{"item_code": "ITEM-007", "qty": 10, "rate": 100, "warehouse": warehouse("WH-RAW01")},
			],
		}
	)
	tmpl = _tax_template("Purchase Taxes and Charges Template", "增值税 13% 进项")
	if tmpl:
		po.taxes_and_charges = tmpl
	po.insert(ignore_permissions=True)
	po.submit()
	update_state(**{key: po.name})
	return po.name


def _purchase_receipt_from_po(po_name: str, state_key: str, posting_key: str) -> str:
	state = load_state()
	if state.get(state_key) and frappe.db.exists("Purchase Receipt", state[state_key]):
		return state[state_key]

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	pr = make_purchase_receipt(po_name)
	pr.posting_date = posting_date(posting_key)
	pr.set_posting_time = 1
	pr.insert(ignore_permissions=True)
	pr.submit()
	update_state(**{state_key: pr.name})
	return pr.name


def _purchase_invoice_from_pr(pr_name: str, state_key: str, posting_key: str) -> str:
	state = load_state()
	if state.get(state_key) and frappe.db.exists("Purchase Invoice", state[state_key]):
		return state[state_key]

	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	pi = make_purchase_invoice(pr_name)
	pi.posting_date = posting_date(posting_key)
	pi.set_posting_time = 1
	pi.insert(ignore_permissions=True)
	pi.submit()
	update_state(**{state_key: pi.name})
	return pi.name


def _payment_for_invoice(party_type: str, party: str, invoice_doctype: str, invoice_name: str, state_key: str, posting_key: str) -> str:
	state = load_state()
	if state.get(state_key) and frappe.db.exists("Payment Entry", state[state_key]):
		return state[state_key]

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	pe = get_payment_entry(invoice_doctype, invoice_name, party_amount=None)
	pe.posting_date = posting_date(posting_key)
	pe.reference_no = invoice_name
	pe.reference_date = posting_date(posting_key)
	pe.set_posting_time = 1
	pe.insert(ignore_permissions=True)
	pe.submit()
	update_state(**{state_key: pe.name})
	return pe.name


def _create_subcontract_po(state: dict) -> str:
	key = "po_sub"
	if state.get(key) and frappe.db.exists("Purchase Order", state[key]):
		return state[key]

	po = frappe.get_doc(
		{
			"doctype": "Purchase Order",
			"company": company(),
			"supplier": "SUB-001",
			"supplier_name": _supplier_name("SUB-001"),
			"is_subcontracted": 1,
			"transaction_date": posting_date("po_sub"),
			"schedule_date": posting_date("subcontract_receipt"),
			"items": [
				{
					"item_code": "SRV-SUB-001",
					"fg_item": "ITEM-008",
					"qty": 50,
					"rate": 20,
					"fg_item_qty": 50,
					"warehouse": warehouse("WH-WIP01"),
					"schedule_date": posting_date("subcontract_receipt"),
				}
			],
		}
	)
	po.set_missing_values()
	po.insert(ignore_permissions=True)
	po.submit()
	update_state(**{key: po.name})
	return po.name


def _create_subcontracting_order(po_name: str, state: dict) -> str:
	key = "subcontract_order"
	if state.get(key) and frappe.db.exists("Subcontracting Order", state[key]):
		return state[key]

	from erpnext.buying.doctype.purchase_order.purchase_order import get_mapped_subcontracting_order

	sco = get_mapped_subcontracting_order(po_name)
	raw_wh = warehouse("WH-RAW01")
	sco.supplier_warehouse = warehouse("WH-SUB01")
	for row in sco.get("supplied_items") or []:
		row.reserve_warehouse = raw_wh
	sco.insert(ignore_permissions=True)
	sco.submit()
	update_state(**{key: sco.name})
	return sco.name


def _transfer_subcontract_materials(sco_name: str, state: dict) -> str:
	key = "subcontract_transfer"
	if state.get(key) and frappe.db.exists("Stock Entry", state[key]):
		return state[key]

	from erpnext.controllers.subcontracting_controller import make_rm_stock_entry

	ste_dict = make_rm_stock_entry(subcontract_order=sco_name)
	ste = frappe.get_doc(ste_dict)
	raw_wh = warehouse("WH-RAW01")
	sub_wh = warehouse("WH-SUB01")
	for item in ste.items:
		item.s_warehouse = raw_wh
		item.t_warehouse = sub_wh
	ste.posting_date = posting_date("po_sub")
	ste.set_posting_time = 1
	ste.insert(ignore_permissions=True)
	ste.submit()
	update_state(**{key: ste.name})
	return ste.name


def _subcontracting_receipt(sco_name: str, state: dict) -> str:
	key = "subcontract_receipt"
	if state.get(key) and frappe.db.exists("Subcontracting Receipt", state[key]):
		return state[key]

	from erpnext.subcontracting.doctype.subcontracting_order.subcontracting_order import (
		make_subcontracting_receipt,
	)

	scr = make_subcontracting_receipt(sco_name)
	from showroom._common import account

	sub_inv = account(account_number="1408")
	cogs = account(account_number="6401")
	raw_wh = warehouse("WH-RAW01")
	for item in scr.items:
		item.warehouse = raw_wh
		item.expense_account = sub_inv
		item.service_expense_account = cogs
	for row in scr.get("supplied_items") or []:
		row.expense_account = sub_inv
	scr.posting_date = posting_date("subcontract_receipt")
	scr.set_posting_time = 1
	scr.insert(ignore_permissions=True)
	scr.submit()
	update_state(**{key: scr.name})
	return scr.name


def _create_work_order(state: dict) -> str:
	key = "work_order"
	if state.get(key) and frappe.db.exists("Work Order", state[key]):
		return state[key]

	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"company": company(),
			"production_item": "ITEM-001",
			"bom_no": frappe.db.get_value("Item", "ITEM-001", "default_bom"),
			"qty": 50,
			"wip_warehouse": warehouse("WH-WIP01"),
			"fg_warehouse": warehouse("WH-FG01"),
			"source_warehouse": warehouse("WH-RAW01"),
			"planned_start_date": posting_date("work_order_start"),
			"expected_delivery_date": posting_date("work_order_end"),
		}
	)
	wo.set_required_items()
	wo.insert(ignore_permissions=True)
	wo.submit()
	update_state(**{key: wo.name})
	return wo.name


def _work_order_stock_entries(wo_name: str, state: dict) -> dict[str, str]:
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
	from showroom._common import account

	result = {}
	for purpose, key, posting_key in (
		("Material Transfer for Manufacture", "wo_transfer", "subcontract_receipt"),
		("Manufacture", "wo_manufacture", "work_order_end"),
	):
		if state.get(key) and frappe.db.exists("Stock Entry", state[key]):
			result[key] = state[key]
			continue
		ste_dict = make_stock_entry(wo_name, purpose, qty=50)
		ste = frappe.get_doc(ste_dict)
		ste.posting_date = posting_date(posting_key)
		ste.set_posting_time = 1
		if purpose == "Manufacture":
			ste.set(
				"additional_costs",
				[
					{
						"expense_account": account(account_number="500102"),
						"description": "直接人工",
						"amount": 5000,
					},
					{
						"expense_account": account(account_number="500103"),
						"description": "制造费用",
						"amount": 3250,
					},
				],
			)
		ste.insert(ignore_permissions=True)
		ste.submit()
		result[key] = ste.name
		update_state(**{key: ste.name})
	return result


def _post_production_overheads(state: dict) -> str | None:
	key = "overhead_je"
	if state.get(key) and frappe.db.exists("Journal Entry", state[key]):
		return state[key]

	from showroom._common import account

	labour = account(account_number="500102")
	mfg = account(account_number="500103")
	mfg_source = account(account_number="1602") or account(account_number="6602")
	if not all([labour, mfg, mfg_source]):
		return None

	je = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"company": company(),
			"posting_date": posting_date("work_order_end"),
			"voucher_type": "Journal Entry",
			"accounts": [
				{"account": labour, "debit_in_account_currency": 5000},
				{"account": mfg_source, "credit_in_account_currency": 5000},
				{"account": mfg, "debit_in_account_currency": 3250},
				{"account": mfg_source, "credit_in_account_currency": 3250},
			],
		}
	)
	je.insert(ignore_permissions=True)
	je.submit()
	update_state(**{key: je.name})
	return je.name


def _delivery_and_invoice(so_name: str, state: dict) -> dict[str, str]:
	result = {}
	if not state.get("delivery_note"):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

		dn = make_delivery_note(so_name)
		dn.posting_date = posting_date("delivery")
		dn.set_posting_time = 1
		dn.insert(ignore_permissions=True)
		dn.submit()
		result["delivery_note"] = dn.name
		update_state(delivery_note=dn.name)
	else:
		result["delivery_note"] = state["delivery_note"]

	if not state.get("sales_invoice"):
		from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

		si = make_sales_invoice(result["delivery_note"])
		si.posting_date = posting_date("sales_invoice")
		si.set_posting_time = 1
		si.insert(ignore_permissions=True)
		si.submit()
		result["sales_invoice"] = si.name
		update_state(sales_invoice=si.name)
	else:
		result["sales_invoice"] = state["sales_invoice"]

	if not state.get("payment_receipt"):
		result["payment_receipt"] = _payment_for_invoice(
			"Customer", "CUST-001", "Sales Invoice", result["sales_invoice"], "payment_receipt", "payment_customer"
		)
	else:
		result["payment_receipt"] = state["payment_receipt"]

	return result


def run_flow() -> dict:
	init_site()
	state = load_state()

	so = _get_or_create_sales_order(state)
	state = load_state()
	mr = _create_material_request(state)
	state = load_state()

	po1 = _create_po_supp1(state)
	state = load_state()
	pr1 = _purchase_receipt_from_po(po1, "purchase_receipt_supp1", "po_receipt")
	state = load_state()
	pi1 = _purchase_invoice_from_pr(pr1, "purchase_invoice_supp1", "po_receipt")
	state = load_state()
	pe1 = _payment_for_invoice("Supplier", "SUPP-001", "Purchase Invoice", pi1, "payment_supp1", "payment_supplier")

	po2 = _create_po_supp2(state)
	state = load_state()
	pr2 = _purchase_receipt_from_po(po2, "purchase_receipt_supp2", "po_receipt")
	state = load_state()
	pi2 = _purchase_invoice_from_pr(pr2, "purchase_invoice_supp2", "po_receipt")
	state = load_state()
	_payment_for_invoice("Supplier", "SUPP-002", "Purchase Invoice", pi2, "payment_supp2", "payment_supplier")

	po_sub = _create_subcontract_po(state)
	state = load_state()
	sco = _create_subcontracting_order(po_sub, state)
	state = load_state()
	_transfer_subcontract_materials(sco, state)
	state = load_state()
	_subcontracting_receipt(sco, state)

	wo = _create_work_order(state)
	state = load_state()
	ste = _work_order_stock_entries(wo, state)
	# Direct labour and manufacturing overhead are capitalized through the
	# Manufacture Stock Entry additional_costs table, matching the sample-room
	# production cost roll-up without a separate manual JE.

	state = load_state()
	fulfillment = _delivery_and_invoice(so, state)

	result = {
		"sales_order": so,
		"material_request": mr,
		"po_supp1": po1,
		"purchase_receipt_supp1": pr1,
		"purchase_invoice_supp1": pi1,
		"payment_supp1": pe1,
		"po_supp2": po2,
		"purchase_receipt_supp2": pr2,
		"purchase_invoice_supp2": pi2,
		"po_sub": po_sub,
		"subcontract_order": sco,
		"subcontract_transfer": state.get("subcontract_transfer"),
		"subcontract_receipt": state.get("subcontract_receipt"),
		"work_order": wo,
		"wo_transfer": ste.get("wo_transfer"),
		"wo_manufacture": ste.get("wo_manufacture"),
		"work_order_stock_entries": ste,
		**fulfillment,
	}
	update_state(flow_result=result)
	commit()
	return result


def run():
	bootstrap_path()
	result = run_flow()
	print(result)
	return result


if __name__ == "__main__":
	run()
