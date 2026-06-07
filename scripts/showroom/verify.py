"""Verify showroom data against demo document expectations."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

import frappe
from frappe.utils import flt

from showroom._common import (
	bootstrap_path,
	cfg,
	company,
	get_bin_qty,
	init_site,
	load_state,
)


def _check(module: str, name: str, expected, actual, tol: float = 0.01) -> dict:
	if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
		status = "Pass" if abs(flt(actual) - flt(expected)) <= tol else "Fail"
	else:
		status = "Pass" if str(expected) == str(actual) else "Fail"
	return {
		"module": module,
		"test_item": name,
		"expected": expected,
		"actual": actual,
		"status": status,
	}


def run_checks() -> list[dict]:
	state = load_state()
	checks: list[dict] = []

	# After full flow raw materials consumed by production
	checks.append(_check("库存", "CPU ITEM-002 WH-RAW01 (post-production)", 0, get_bin_qty("ITEM-002", "WH-RAW01")))
	checks.append(_check("库存", "主板 ITEM-003 WH-RAW01 (post-production)", 0, get_bin_qty("ITEM-003", "WH-RAW01")))

	# After full flow FG should be 0 (delivered 50)
	checks.append(_check("库存", "成品 ITEM-001 WH-FG01", 0, get_bin_qty("ITEM-001", "WH-FG01")))

	# Sales order qty
	so = state.get("sales_order") or state.get("flow_result", {}).get("sales_order")
	if so and frappe.db.exists("Sales Order", so):
		qty = frappe.db.get_value("Sales Order Item", {"parent": so, "item_code": "ITEM-001"}, "qty")
		checks.append(_check("销售", "SO qty ITEM-001", 50, qty))

	# Work order qty
	wo = state.get("work_order") or state.get("flow_result", {}).get("work_order")
	if wo and frappe.db.exists("Work Order", wo):
		checks.append(_check("生产", "WO qty", 50, frappe.db.get_value("Work Order", wo, "qty")))

	# Delivery note qty
	dn = state.get("delivery_note") or state.get("flow_result", {}).get("delivery_note")
	if dn and frappe.db.exists("Delivery Note", dn):
		dqty = frappe.db.get_value("Delivery Note Item", {"parent": dn, "item_code": "ITEM-001"}, "qty")
		checks.append(_check("销售", "DN qty ITEM-001", 50, dqty))

	# Sales invoice total
	si = state.get("sales_invoice") or state.get("flow_result", {}).get("sales_invoice")
	if si and frappe.db.exists("Sales Invoice", si):
		inv = frappe.get_doc("Sales Invoice", si)
		checks.append(_check("财务", "SI grand_total", 197750, inv.grand_total))
		checks.append(_check("财务", "SI net_total", 175000, inv.net_total))
		checks.append(_check("财务", "SI outstanding after payment", 0, inv.outstanding_amount))

	# Purchase invoice SUPP-001
	pi = state.get("purchase_invoice_supp1") or state.get("flow_result", {}).get("purchase_invoice_supp1")
	if pi and frappe.db.exists("Purchase Invoice", pi):
		pinv = frappe.get_doc("Purchase Invoice", pi)
		checks.append(_check("财务", "PI SUPP-001 grand_total", 85880, pinv.grand_total))
		checks.append(_check("财务", "PI SUPP-001 outstanding", 0, pinv.outstanding_amount))

	# MRP net requirements (static from doc)
	mrp_expected = {
		"ITEM-002": 40,
		"ITEM-003": 35,
		"ITEM-004": 70,
		"ITEM-005": 30,
		"ITEM-006": 25,
		"ITEM-007": 10,
		"ITEM-008": 50,
	}
	mr = state.get("material_request") or state.get("flow_result", {}).get("material_request")
	if mr and frappe.db.exists("Material Request", mr):
		for item, exp in mrp_expected.items():
			qty = frappe.db.get_value("Material Request Item", {"parent": mr, "item_code": item}, "qty")
			checks.append(_check("MRP", f"MR net {item}", exp, qty))

	return checks


def write_report(checks: list[dict]) -> Path:
	report_rel = cfg("verification_report", "../../doc/showroom-verification-report.md")
	report_path = (Path(__file__).resolve().parent / report_rel).resolve()
	report_path.parent.mkdir(parents=True, exist_ok=True)

	passed = sum(1 for c in checks if c["status"] == "Pass")
	failed = len(checks) - passed
	lines = [
		"# 制造行业样板间验证报告",
		"",
		f"- 公司：{company()}",
		f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
		f"- 汇总：**{passed} Pass / {failed} Fail**（共 {len(checks)} 项）",
		"",
		"## 测试验证清单",
		"",
		"| 模块 | 测试项 | 预期 | 实际 | 状态 |",
		"| --- | --- | --- | --- | --- |",
	]
	for row in checks:
		lines.append(
			f"| {row['module']} | {row['test_item']} | {row['expected']} | {row['actual']} | {row['status']} |"
		)

	lines.extend(
		[
			"",
			"## 文档对照 §6",
			"",
			"| 流程模块 | 状态 |",
			"| --- | --- |",
			f"| 基础档案 | {'Pass' if failed == 0 else '部分'} |",
			f"| 销售流程 | {'Pass' if all(c['status']=='Pass' for c in checks if c['module']=='销售') else 'Fail'} |",
			f"| 采购流程 | {'Pass' if all(c['status']=='Pass' for c in checks if c['module'] in ('MRP','财务') and 'PI' in c['test_item']) else '部分'} |",
			f"| 生产流程 | {'Pass' if all(c['status']=='Pass' for c in checks if c['module']=='生产') else '部分'} |",
			f"| 数据一致性 | {'Pass' if failed == 0 else 'Fail'} |",
		]
	)

	report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
	return report_path


def verify() -> dict:
	init_site()
	checks = run_checks()
	report = write_report(checks)
	passed = sum(1 for c in checks if c["status"] == "Pass")
	return {"checks": len(checks), "passed": passed, "failed": len(checks) - passed, "report": str(report)}


def run():
	bootstrap_path()
	result = verify()
	print(result)
	return result


if __name__ == "__main__":
	run()
