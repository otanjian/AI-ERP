"""Serve ERPNext E-R diagram in Help menu."""

from pathlib import Path

import frappe

ER_DIAGRAM_LABEL = "数据库 E-R 图"
ER_DIAGRAM_ROUTE = "/assets/frappe_assistant_core/erpnext-er-diagram.html"
PUBLIC_HTML = (
	Path(frappe.get_app_path("frappe_assistant_core")) / "public" / "erpnext-er-diagram.html"
)


def ensure_er_diagram_help_link():
	"""Add Help menu entry pointing to the static E-R diagram page."""
	navbar = frappe.get_single("Navbar Settings")
	for item in navbar.help_dropdown:
		if item.route == ER_DIAGRAM_ROUTE or item.item_label == ER_DIAGRAM_LABEL:
			return

	navbar.append(
		"help_dropdown",
		{
			"item_label": ER_DIAGRAM_LABEL,
			"item_type": "Route",
			"route": ER_DIAGRAM_ROUTE,
			"is_standard": 0,
		},
	)
	navbar.save(ignore_permissions=True)
	frappe.clear_cache(doctype="Navbar Settings")
