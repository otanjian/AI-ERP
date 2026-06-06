#!/usr/bin/env python3
"""Re-publish homepage from homepage_optimized.html. Run from bench root:

cd /home/frappe/frappe-bench && ./env/bin/python sites/west.bosofts.com/republish_homepage.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parents[2]
SITE = "west.bosofts.com"

PAGE_TITLE = "AI ERP|博软（杭州）科技有限公司"
META_DESCRIPTION = (
	"BOWIAI免费AI+ERP SaaS系统，基于ERPNext开源底座，自研AI智能框架，提供财务、采购、销售、库存、制造全流程一体化管理，"
	"永久免费使用，2-6周落地见效"
)
META_KEYWORDS = "免费AI ERP,ERP SaaS,中小企业免费ERP,制造ERP,智能进销存,开源ERP,AI经营分析"


def upsert_home_route_keywords(frappe, route: str) -> None:
	"""Inject <meta name=\"keywords\" ...> via Website Route Meta (homepage path resolves to home_page)."""
	if not route:
		return
	if frappe.db.exists("Website Route Meta", route):
		doc = frappe.get_doc("Website Route Meta", route)
		doc.meta_tags = [r for r in doc.meta_tags if (getattr(r, "key", None) or "") != "keywords"]
		doc.append("meta_tags", {"key": "keywords", "value": META_KEYWORDS})
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("Website Route Meta")
		doc.append("meta_tags", {"key": "keywords", "value": META_KEYWORDS})
		doc.insert(ignore_permissions=True, set_name=route)


def main() -> None:
	os.environ["FRAPPE_STREAM_LOGGING"] = "1"
	os.chdir(BENCH_ROOT)
	sys.path.insert(0, str(BENCH_ROOT / "apps"))
	import frappe

	frappe.init(site=SITE, sites_path=str(BENCH_ROOT / "sites"), force=True)
	frappe.connect()

	html_path = BENCH_ROOT / "sites" / SITE / "homepage_optimized.html"
	html = html_path.read_text(encoding="utf-8")
	doc = frappe.get_doc("Web Page", "ai-erp-智能经营平台")
	doc.title = PAGE_TITLE
	doc.meta_title = PAGE_TITLE
	doc.meta_description = META_DESCRIPTION
	doc.main_section_html = html
	doc.save(ignore_permissions=True)

	home_route = frappe.db.get_single_value("Website Settings", "home_page") or doc.route
	upsert_home_route_keywords(frappe, home_route)

	frappe.db.commit()
	frappe.clear_cache(doctype="Web Page")
	frappe.clear_cache(doctype="Website Route Meta")
	print("OK:", doc.route, "| title len:", len(doc.title), "| route meta:", home_route)


if __name__ == "__main__":
	main()
