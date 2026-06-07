"""Cancel showroom flow vouchers so they can be re-posted with corrected accounts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showroom._common import bootstrap_path, commit, init_site, load_config, load_state, save_state

# Cancel in reverse dependency order.
FLOW_DOC_KEYS = [
	("payment_receipt", "Payment Entry"),
	("payment_supp2", "Payment Entry"),
	("payment_supp1", "Payment Entry"),
	("sales_invoice", "Sales Invoice"),
	("delivery_note", "Delivery Note"),
	("overhead_je", "Journal Entry"),
	("wo_manufacture", "Stock Entry"),
	("wo_transfer", "Stock Entry"),
	("work_order", "Work Order"),
	("subcontract_receipt", "Subcontracting Receipt"),
	("subcontract_transfer", "Stock Entry"),
	("subcontract_order", "Subcontracting Order"),
	("purchase_invoice_supp2", "Purchase Invoice"),
	("purchase_receipt_supp2", "Purchase Receipt"),
	("po_supp2", "Purchase Order"),
	("purchase_invoice_supp1", "Purchase Invoice"),
	("purchase_receipt_supp1", "Purchase Receipt"),
	("po_supp1", "Purchase Order"),
	("po_sub", "Purchase Order"),
	("material_request", "Material Request"),
	("sales_order", "Sales Order"),
]

FLOW_STATE_KEYS = [k for k, _ in FLOW_DOC_KEYS] + ["flow_result"]


def _resolve_name(state: dict, key: str) -> str | None:
	name = state.get(key)
	if not name:
		name = (state.get("flow_result") or {}).get(key)
	return name


def cancel_flow() -> dict[str, str]:
	import frappe

	init_site()
	state = load_state()
	cancelled: dict[str, str] = {}

	for key, doctype in FLOW_DOC_KEYS:
		name = _resolve_name(state, key)
		if not name or not frappe.db.exists(doctype, name):
			continue
		doc = frappe.get_doc(doctype, name)
		if doc.docstatus != 1:
			if doc.docstatus == 0:
				doc.delete()
				cancelled[key] = f"deleted draft {name}"
			continue
		try:
			doc.cancel()
			cancelled[key] = name
		except Exception as exc:
			cancelled[key] = f"FAILED {name}: {exc}"

	for key in FLOW_STATE_KEYS:
		state.pop(key, None)
	save_state(state)
	commit()
	return cancelled


def run():
	bootstrap_path()
	load_config()
	result = cancel_flow()
	print(result)
	return result


if __name__ == "__main__":
	run()
