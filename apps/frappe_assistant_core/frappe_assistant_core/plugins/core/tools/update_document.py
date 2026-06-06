# Frappe Assistant Core - AI Assistant integration for Frappe Framework
# Copyright (C) 2025 Paul Clinton
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Document Update Tool for Core Plugin.
Updates existing Frappe documents.
"""

from typing import Any, Dict

import frappe
from frappe import _

from frappe_assistant_core.core.base_tool import BaseTool


class DocumentUpdate(BaseTool):
    """
    Tool for updating existing Frappe documents.

    Provides capabilities for:
    - Updating document field values
    - Checking permissions
    - Handling validation errors
    """

    def __init__(self):
        super().__init__()
        self.name = "update_document"
        self.description = "Update/modify an existing Frappe document. Use when users want to change field values in an existing record. Always fetch the document first to understand current values."
        self.requires_permission = None  # Permission checked dynamically per DocType

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {
                    "type": "string",
                    "description": "The Frappe DocType name (e.g., 'Customer', 'Sales Invoice', 'Item')",
                },
                "name": {
                    "type": "string",
                    "description": "The document name/ID to update (e.g., 'CUST-00001', 'SINV-00001')",
                },
                "data": {
                    "type": "object",
                    "description": "Field updates as key-value pairs. Only include fields that need to be changed. Example: {'customer_name': 'Updated Corp Name', 'phone': '+1234567890'}",
                },
            },
            "required": ["doctype", "name", "data"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document"""
        doctype = arguments.get("doctype")
        name = arguments.get("name")
        data = arguments.get("data", {})

        # Import security validation
        from frappe_assistant_core.core.security_config import (
            filter_sensitive_fields,
            validate_document_access,
        )

        # Validate document access with comprehensive permission checking
        validation_result = validate_document_access(
            user=frappe.session.user, doctype=doctype, name=name, perm_type="write"
        )

        if not validation_result["success"]:
            return validation_result

        user_role = validation_result["role"]

        try:
            # Check if document exists
            if not frappe.db.exists(doctype, name):
                result = {"success": False, "error": f"{doctype} '{name}' not found"}
                return result

            # Get document
            doc = frappe.get_doc(doctype, name)

            # Enhanced document state validation
            current_docstatus = getattr(doc, "docstatus", 0)
            current_workflow_state = getattr(doc, "workflow_state", None)

            # Check if document is submitted (protection against editing submitted docs)
            if current_docstatus == 1:
                result = {
                    "success": False,
                    "error": f"Cannot modify submitted document {doctype} '{name}'. Submitted documents are read-only.",
                    "docstatus": current_docstatus,
                    "workflow_state": current_workflow_state,
                    "suggestion": "Use document_get to view the submitted document, or create a new document if needed.",
                }
                return result

            # Check if document is cancelled
            if current_docstatus == 2:
                result = {
                    "success": False,
                    "error": f"Cannot modify cancelled document {doctype} '{name}'. Cancelled documents are read-only.",
                    "docstatus": current_docstatus,
                    "workflow_state": current_workflow_state,
                    "suggestion": "Use document_get to view the cancelled document, or create a new document if needed.",
                }
                return result

            # Provide helpful information about document state
            doc_state_info = {
                "docstatus": current_docstatus,
                "state_description": "Draft" if current_docstatus == 0 else "Unknown",
                "workflow_state": current_workflow_state,
                "is_editable": current_docstatus == 0,
            }

            # Filter out sensitive fields that user shouldn't be able to update
            from frappe_assistant_core.core.security_config import ADMIN_ONLY_FIELDS, SENSITIVE_FIELDS

            # Get restricted fields for this role and doctype
            restricted_fields = set()
            restricted_fields.update(SENSITIVE_FIELDS.get("all_doctypes", []))
            restricted_fields.update(SENSITIVE_FIELDS.get(doctype, []))

            if user_role == "Assistant User":
                restricted_fields.update(ADMIN_ONLY_FIELDS.get("all_doctypes", []))
                doctype_admin_fields = ADMIN_ONLY_FIELDS.get(doctype, [])
                if doctype_admin_fields != "*":
                    restricted_fields.update(doctype_admin_fields)

            # Check for attempts to update restricted fields
            restricted_updates = [field for field in data.keys() if field in restricted_fields]
            if restricted_updates:
                result = {
                    "success": False,
                    "error": f"Cannot update restricted fields: {', '.join(restricted_updates)}. These fields require higher privileges.",
                }
                return result

            # Update field values
            for field, value in data.items():
                setattr(doc, field, value)

            # Save document
            doc.save()

            # Get updated document state
            doc.reload()
            updated_docstatus = getattr(doc, "docstatus", 0)
            updated_workflow_state = getattr(doc, "workflow_state", None)

            result = {
                "success": True,
                "name": doc.name,
                "doctype": doctype,
                "updated_fields": list(data.keys()),
                "docstatus": updated_docstatus,
                "state_description": "Draft" if updated_docstatus == 0 else "Unknown",
                "workflow_state": updated_workflow_state,
                "owner": doc.owner,
                "modified": str(doc.modified),
                "modified_by": doc.modified_by,
                "message": f"{doctype} '{doc.name}' updated successfully",
            }

            # Check if user can submit this document
            if updated_docstatus == 0:  # Only for draft documents
                try:
                    result["can_submit"] = frappe.has_permission(doctype, "submit", doc=doc.name)
                except Exception:
                    result["can_submit"] = False
            else:
                result["can_submit"] = False

            # Add useful next steps information
            if updated_docstatus == 0:
                result["next_steps"] = [
                    "Document remains in draft state",
                    "You can continue updating this document",
                    f"Submit permission: {'Available' if result['can_submit'] else 'Not available'}",
                ]

                # Add workflow actions if available
                if updated_workflow_state:
                    result["next_steps"].append(f"Current workflow state: {updated_workflow_state}")
            else:
                result["next_steps"] = [
                    f"Document state: {result['state_description']}",
                    "Further modifications may be restricted",
                ]

            # Log successful update
            return result

        except Exception as e:
            frappe.log_error(
                title=_("Document Update Error"), message=f"Error updating {doctype} '{name}': {str(e)}"
            )

            result = {"success": False, "error": str(e), "doctype": doctype, "name": name}

            # Log failed update
            return result


# Make sure class name matches file name for discovery
document_update = DocumentUpdate
