import frappe


def execute():
	migrated_routes = frappe.db.get_all("Wiki Document", pluck="route")
	# Filter out None values - SQL NOT IN fails when list contains NULL
	migrated_routes = [r for r in migrated_routes if r is not None]
	orphan_pages = frappe.db.get_all(
		"Wiki Page",
		filters={"route": ["not in", migrated_routes]},
		pluck="name",
	)

	for page in orphan_pages:
		wiki_page = frappe.get_doc("Wiki Page", page)
		wiki_page._migrate_to_wiki_document()
		frappe.db.commit()
