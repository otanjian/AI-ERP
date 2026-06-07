"""Compare GL entries against showroom doc expectations."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent.parent
import os
import sys

os.chdir(BENCH_DIR / "sites")
sys.path.insert(0, str(BENCH_DIR / "apps" / "frappe"))
sys.path.insert(0, str(BENCH_DIR / "apps" / "erpnext"))
sys.path.insert(0, str(BENCH_DIR / "scripts"))

import frappe
from showroom._common import bootstrap_path, init_site, load_config, load_state

COMPANY = "智联电脑组装有限公司"

# voucher_type -> {voucher_no from state key: (expected description, [(account_number_prefix, debit, credit), ...])}
# Amounts None = just check account presence and side
CHECKS = {
	"Delivery Note": {
		"delivery_note": {
			"desc": "销售出库 借6401贷1405",
			"expected_total_debit": None,
			"accounts": [("6401", "debit"), ("1405", "credit")],
		}
	},
	"Sales Invoice": {
		"sales_invoice": {
			"desc": "销售发票",
			"lines": [
				("1122", 197750, 0),
				("6001", 0, 175000),
				("22210105", 0, 22750),
			],
		}
	},
	"Payment Entry": {
		"payment_receipt": {
			"desc": "客户收款",
			"lines": [("1002", 197750, 0), ("1122", 0, 197750)],
		},
		"payment_supp1": {
			"desc": "SUPP-001付款",
			"lines": [("2202", 85880, 0), ("1002", 0, 85880)],
		},
	},
	"Purchase Receipt": {
		"purchase_receipt_supp1": {
			"desc": "采购入库暂估 CPU/主板",
			"accounts": [("1403", "debit"), ("2202", "credit")],
			"doc_amount": 76000,
		}
	},
	"Purchase Invoice": {
		"purchase_invoice_supp1": {
			"desc": "采购发票 SUPP-001",
			"lines": [
				("22210101", 9880, 0),
				("220202", 76000, 0),
				("220201", 0, 85880),
			],
		}
	},
	"Stock Entry": {
		"wo_manufacture": {
			"desc": "生产入库 借1405贷5001",
			"accounts": [("1405", "debit"), ("5001", "credit")],
		},
		"subcontract_transfer": {
			"desc": "委外材料调拨 借1408贷1403",
			"accounts": [("1408", "debit"), ("1403", "credit")],
			"doc_amount": 750,  # doc v2: 500+250; doc v1: 3000
		},
	},
	"Subcontracting Receipt": {
		"subcontract_receipt": {
			"desc": "委外成品入库",
			"accounts": [("1403", "debit"), ("1408", "credit")],
		}
	},
	"Journal Entry": {
		"overhead_je": {
			"desc": "人工制造费用 JE",
			"accounts": [("50010102", "debit"), ("50010103", "debit"), ("5101", "credit")],
		}
	},
}


def acct_num(account_name: str) -> str:
	return frappe.db.get_value("Account", account_name, "account_number") or ""


def gl_by_voucher(voucher_type: str, voucher_no: str) -> list[dict]:
	rows = frappe.get_all(
		"GL Entry",
		filters={
			"company": COMPANY,
			"voucher_type": voucher_type,
			"voucher_no": voucher_no,
			"is_cancelled": 0,
		},
		fields=["account", "debit", "credit", "debit_in_account_currency", "credit_in_account_currency"],
	)
	for r in rows:
		r["account_number"] = acct_num(r["account"])
	return rows


def summarize_gl(rows: list[dict]) -> dict[str, dict]:
	agg: dict[str, dict] = defaultdict(lambda: {"debit": 0.0, "credit": 0.0, "name": ""})
	for r in rows:
		num = str(r.get("account_number") or "")
		agg[num]["debit"] += float(r["debit"] or 0)
		agg[num]["credit"] += float(r["credit"] or 0)
		agg[num]["name"] = r["account"]
	return dict(agg)


def match_lines(agg: dict, lines: list[tuple], tol: float = 0.01) -> list[str]:
	issues = []
	for num, exp_d, exp_c in lines:
		key = None
		num_str = str(num)
		for k in sorted(agg.keys(), key=lambda x: len(x or ""), reverse=True):
			if not k:
				continue
			if k == num_str or k.startswith(num_str) or num_str.startswith(k):
				# Avoid 220201 matching 220202 via shared "2202" prefix
				if len(num_str) >= 6 and len(k) >= 6 and k[:6] != num_str[:6]:
					continue
				key = k
				break
		if key is None:
			issues.append(f"  缺少科目 {num}")
			continue
		a = agg[key]
		if abs(a["debit"] - exp_d) > tol or abs(a["credit"] - exp_c) > tol:
			issues.append(
				f"  科目 {num}({a['name']}): 期望借{exp_d}/贷{exp_c}, 实际借{a['debit']}/贷{a['credit']}"
			)
	return issues


def match_accounts(agg: dict, specs: list[tuple]) -> list[str]:
	issues = []
	for num, side in specs:
		found = False
		for k, v in agg.items():
			if not str(k).startswith(str(num)):
				continue
			found = True
			if side == "debit" and v["debit"] <= 0:
				issues.append(f"  科目 {num} 应有借方, 实际借{v['debit']}")
			if side == "credit" and v["credit"] <= 0:
				issues.append(f"  科目 {num} 应有贷方, 实际贷{v['credit']}")
		if not found:
			issues.append(f"  缺少科目 {num}")
	return issues


def run():
	bootstrap_path()
	load_config()
	init_site()
	return _run_checks()


def _run_checks():

	print("=" * 60)
	print("GL 凭证检查 — 智联电脑组装有限公司")
	print("=" * 60)

	state = load_state()
	all_issues = []

	for vtype, vouchers in CHECKS.items():
		for state_key, spec in vouchers.items():
			vno = state.get(state_key) or state.get("flow_result", {}).get(state_key)
			if not vno:
				print(f"\n[SKIP] {spec['desc']}: 无单据 {state_key}")
				continue
			rows = gl_by_voucher(vtype, vno)
			if not rows:
				print(f"\n[FAIL] {spec['desc']} ({vtype} {vno}): 无 GL 分录")
				all_issues.append(f"{vno}: 无GL")
				continue

			agg = summarize_gl(rows)
			print(f"\n--- {spec['desc']} | {vtype} {vno} ---")
			for k in sorted(agg.keys(), key=lambda x: x or ""):
				v = agg[k]
				if v["debit"] or v["credit"]:
					print(f"  {k:10} {v['name'][:40]:40} 借 {v['debit']:>12,.2f}  贷 {v['credit']:>12,.2f}")

			issues = []
			if "lines" in spec:
				issues = match_lines(agg, spec["lines"])
			if "accounts" in spec:
				issues.extend(match_accounts(agg, spec["accounts"]))
			if spec.get("doc_amount"):
				total_d = sum(v["debit"] for v in agg.values())
				doc_amt = spec["doc_amount"]
				if abs(total_d - doc_amt) > 0.01:
					issues.append(f"  文档金额 {doc_amt:,.2f} vs 实际借方合计 {total_d:,.2f}")

			if issues:
				print("  >> 差异:")
				for i in issues:
					print(i)
				all_issues.extend([f"{vno}: {i.strip()}" for i in issues])
			else:
				print("  >> 科目结构: OK")

	# Extra: list vouchers with no GL in flow
	print("\n" + "=" * 60)
	print(f"汇总: {len(all_issues)} 项差异/待核")
	if all_issues:
		for i in all_issues[:30]:
			print(f"  - {i}")


if __name__ == "__main__":
	run()
