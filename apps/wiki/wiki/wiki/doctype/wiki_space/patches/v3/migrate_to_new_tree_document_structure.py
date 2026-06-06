import frappe


def execute():
	spaces = frappe.db.get_all("Wiki Space", filters={"root_group": ["is", "not set"]}, pluck="name")
	for space in spaces:
		frappe.get_doc("Wiki Space", space).migrate_to_v3()
		frappe.db.commit()
