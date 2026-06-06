# Copyright (c) 2020, Frappe and contributors
# For license information, please see license.txt
import frappe
from frappe.website.website_generator import WebsiteGenerator


class WikiPage(WebsiteGenerator):
	def validate(self):
		frappe.throw(
			frappe._(
				"Wiki Page doctype is deprecated and will be deleted in a future release. Please migrate to Wiki Document (Version 3 structure)."
			)
		)

	def _migrate_to_wiki_document(self):
		frappe.get_doc(
			{
				"doctype": "Wiki Document",
				"title": self.title,
				"content": self.content,
				"route": self.route,
				"is_group": 0,
				"is_published": self.published,
				"is_private": not self.allow_guest,
			}
		).insert()
