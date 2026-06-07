#!/usr/bin/env python3
"""CLI entry for showroom scripts — runs inside bench context without modifying apps."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent.parent
SITES_DIR = BENCH_DIR / "sites"
os.chdir(SITES_DIR)
(BENCH_DIR / "logs").mkdir(exist_ok=True)
sys.path.insert(0, str(BENCH_DIR / "apps" / "frappe"))
sys.path.insert(0, str(BENCH_DIR / "apps" / "erpnext"))
sys.path.insert(0, str(BENCH_DIR / "scripts"))

COMMANDS = {
	"setup_coa": "showroom.setup_coa",
	"setup_settings": "showroom.setup_settings",
	"setup_masters": "showroom.setup_masters",
	"account_defaults": "showroom.account_defaults",
	"cancel_flow": "showroom.cancel_flow",
	"run_flow": "showroom.run_flow",
	"verify": "showroom.verify",
	"check_gl": "showroom.check_gl",
}


def main() -> None:
	if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
		print(f"Usage: cli.py [{'|'.join(COMMANDS)}]")
		sys.exit(1)

	# Bootstrap frappe before importing erpnext-dependent modules.
	import frappe
	from showroom._common import cfg, load_config

	load_config()
	site = os.environ.get("SITE") or cfg("site")
	frappe.init(site=site, sites_path=".")
	frappe.connect()
	frappe.set_user("Administrator")
	frappe.flags.ignore_permissions = True

	module_path = COMMANDS[sys.argv[1]]
	mod = __import__(module_path, fromlist=["run"])
	result = mod.run()
	if frappe.db:
		frappe.db.commit()
	if result is not None:
		print(result)


if __name__ == "__main__":
	main()
