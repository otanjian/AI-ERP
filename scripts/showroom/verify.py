"""Verify showroom data against demo document expectations."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

import frappe
from frappe.utils import flt

from showroom._common import (
	account,
	bootstrap_path,
	cfg,
	company,
	get_bin_qty,
	init_site,
	load_fixture,
	load_state,
	warehouse,
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

	company_doc = frappe.db.get_value(
		"Company",
		company(),
		["country", "default_currency", "chart_of_accounts"],
		as_dict=True,
	)
	checks.append(_check("基础档案", "公司存在", True, bool(company_doc)))
	if company_doc:
		checks.append(_check("基础档案", "国家 China", "China", company_doc.country))
		checks.append(_check("基础档案", "币种 CNY", "CNY", company_doc.default_currency))
		checks.append(_check("财务", "会计准则", "中国企业会计准则", company_doc.chart_of_accounts))

	required_accounts = {
		"1122": "应收账款",
		"1221": "其他应收款",
		"1403": "原材料",
		"1408": "委托加工物资",
		"1405": "库存商品",
		"1602": "累计折旧",
		"2202": "应付账款",
		"2221": "应交税费",
		"222101": "应交增值税",
		"22210101": "进项税额",
		"22210105": "销项税额",
		"222112": "应交所得税",
		"2211": "应付职工薪酬",
		"1002": "银行存款",
		"5001": "生产成本",
		"500101": "直接材料",
		"500102": "直接人工",
		"500103": "制造费用",
		"6001": "主营业务收入",
		"6401": "主营业务成本",
		"6602": "管理费用",
		"6801": "所得税费用",
		"4103": "本年利润",
	}
	for number, name in required_accounts.items():
		acct = account(account_number=number)
		actual = frappe.db.get_value("Account", acct, "account_name") if acct else None
		checks.append(_check("财务", f"科目 {number}", name, actual))

	for template in ("增值税 13% 销项", "增值税 13% 进项"):
		dt = "Sales Taxes and Charges Template" if "销项" in template else "Purchase Taxes and Charges Template"
		checks.append(_check("财务", f"税模板 {template}", True, bool(frappe.db.exists(dt, {"title": template, "company": company()}))))

	for row in load_fixture("warehouses.json"):
		checks.append(_check("基础档案", f"仓库 {row['warehouse_name']}", True, bool(frappe.db.exists("Warehouse", {"warehouse_name": row["warehouse_name"], "company": company()}))))

	for row in load_fixture("items.json"):
		checks.append(_check("基础档案", f"物料 {row['item_code']}", row["item_name"], frappe.db.get_value("Item", row["item_code"], "item_name")))

	for row in load_fixture("boms.json"):
		default_bom = frappe.db.get_value("Item", row["item"], "default_bom")
		checks.append(_check("基础档案", f"BOM {row['item']}", True, bool(default_bom and frappe.db.exists("BOM", default_bom))))

	flow = state.get("flow_result") or {}
	full_flow_exists = (
		flow.get("sales_order")
		and flow.get("sales_invoice")
		and frappe.db.exists("Sales Order", flow.get("sales_order"))
		and frappe.db.exists("Sales Invoice", flow.get("sales_invoice"))
	)
	if not full_flow_exists:
		for row in load_fixture("opening_stock.json"):
			checks.append(
				_check(
					"库存",
					f"期初 {row['item_code']} {row['warehouse']}",
					row["qty"],
					get_bin_qty(row["item_code"], row["warehouse"]),
				)
			)
		return checks

	for row in load_fixture("opening_stock.json"):
		exists = frappe.db.exists(
			"Stock Reconciliation Item",
			{
				"item_code": row["item_code"],
				"warehouse": warehouse(row["warehouse"]),
				"qty": row["qty"],
			},
		)
		checks.append(_check("库存", f"期初导入记录 {row['item_code']} {row['warehouse']}", True, bool(exists)))

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
		heat_module_consumed = frappe.db.get_value(
			"Work Order Item", {"parent": wo, "item_code": "ITEM-008"}, "consumed_qty"
		)
		checks.append(_check("生产", "总装消耗散热模组 ITEM-008", 50, heat_module_consumed))

	scr = state.get("subcontract_receipt") or state.get("flow_result", {}).get("subcontract_receipt")
	if scr and frappe.db.exists("Subcontracting Receipt", scr):
		doc = frappe.get_doc("Subcontracting Receipt", scr)
		item_qty = sum(flt(row.qty) for row in doc.items if row.item_code == "ITEM-008")
		checks.append(_check("生产", "委外完成散热模组 ITEM-008", 50, item_qty))

	transfer = state.get("wo_transfer") or state.get("flow_result", {}).get("wo_transfer")
	mfg = state.get("wo_manufacture") or state.get("flow_result", {}).get("wo_manufacture")
	if scr and transfer and frappe.db.exists("Subcontracting Receipt", scr) and frappe.db.exists("Stock Entry", transfer):
		scr_date = frappe.db.get_value("Subcontracting Receipt", scr, "posting_date")
		transfer_date = frappe.db.get_value("Stock Entry", transfer, "posting_date")
		checks.append(_check("生产", "散热模组先于成品总装领料", True, bool(scr_date and transfer_date and scr_date <= transfer_date)))

	if scr and mfg and frappe.db.exists("Subcontracting Receipt", scr) and frappe.db.exists("Stock Entry", mfg):
		scr_date = frappe.db.get_value("Subcontracting Receipt", scr, "posting_date")
		mfg_date = frappe.db.get_value("Stock Entry", mfg, "posting_date")
		checks.append(_check("生产", "散热模组先于成品总装", True, bool(scr_date and mfg_date and scr_date <= mfg_date)))

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

	# Manufacturing valuation: material 151,750 + labour 5,000 + overhead 3,250
	if mfg and frappe.db.exists("Stock Entry", mfg):
		doc = frappe.get_doc("Stock Entry", mfg)
		fg_amount = sum(flt(row.basic_amount) + flt(row.additional_cost) for row in doc.items if row.is_finished_item)
		checks.append(_check("生产", "生产入库成品成本", 160000, fg_amount))
		checks.append(_check("生产", "生产入库附加成本", 8250, doc.total_additional_costs))

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
