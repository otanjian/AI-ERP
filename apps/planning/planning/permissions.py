import frappe


def has_app_permission() -> bool:
	if frappe.session.user == "Guest":
		return False

	if frappe.has_permission("Workspace", "read"):
		return True

	return bool(
		set(frappe.get_roles()) & {
			"MRP Planner",
			"MRP Supervisor",
			"MRP Data Administrator",
			"Planning System Administrator",
			"System Manager",
		}
	)
