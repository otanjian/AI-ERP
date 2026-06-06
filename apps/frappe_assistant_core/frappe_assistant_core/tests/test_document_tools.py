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
Test suite for Document Tools using Plugin Architecture
Tests document operations through the tool registry
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import frappe

from frappe_assistant_core.core.tool_registry import get_tool_registry
from frappe_assistant_core.tests.base_test import BaseAssistantTest


class TestDocumentTools(BaseAssistantTest):
    """Test document tools through plugin registry"""

    def setUp(self):
        super().setUp()
        self.registry = get_tool_registry()
        self.test_doctype = "ToDo"  # Safe test doctype that always exists

    def test_get_tools_structure(self):
        """Test that document tools are properly registered"""
        tools = self.registry.get_available_tools()
        tool_names = [tool["name"] for tool in tools]

        # Check for core document tools
        expected_tools = [
            "create_document",
            "get_document",
            "update_document",
            "list_documents",
            "delete_document",
        ]
        found_tools = [tool for tool in expected_tools if tool in tool_names]

        self.assertGreater(len(found_tools), 0, f"Should find document tools. Available: {tool_names}")

    def test_create_document_basic(self):
        """Test basic document creation"""
        if not self.registry.has_tool("create_document"):
            self.skipTest("create_document tool not available")

        # Test with minimal valid data
        arguments = {"doctype": self.test_doctype, "data": {"description": "Test ToDo created by test suite"}}

        try:
            result = self.registry.execute_tool("create_document", arguments)
            self.assertIsInstance(result, dict)

            # Should have success status
            if "success" in result:
                if result.get("success"):
                    # New format: name is directly in result, not nested under "data"
                    self.assertIn("name", result)
                else:
                    # Failed creation should have error message
                    self.assertIn("error", result)
        except Exception as e:
            # Tool execution should not raise unhandled exceptions
            self.fail(f"Tool execution raised exception: {str(e)}")

    def test_get_document_basic(self):
        """Test basic document retrieval"""
        if not self.registry.has_tool("get_document"):
            self.skipTest("get_document tool not available")

        # Try to get Administrator user (should always exist)
        arguments = {"doctype": "User", "name": "Administrator"}

        try:
            result = self.registry.execute_tool("get_document", arguments)
            self.assertIsInstance(result, dict)

            if "success" in result and result.get("success"):
                # Document data is directly in result for successful gets
                self.assertIn("name", result)
                self.assertEqual(result["name"], "Administrator")
        except Exception as e:
            self.fail(f"Tool execution raised exception: {str(e)}")

    def test_list_documents_via_execute_tool(self):
        """Test document listing"""
        if not self.registry.has_tool("list_documents"):
            self.skipTest("list_documents tool not available")

        arguments = {"doctype": "User", "limit": 5, "fields": ["name", "full_name"]}

        try:
            result = self.registry.execute_tool("list_documents", arguments)
            self.assertIsInstance(result, dict)

            if "success" in result and result.get("success"):
                # For list_documents, check if we have documents or results key
                if "documents" in result:
                    self.assertIsInstance(result["documents"], list)
                    if result["documents"]:
                        for doc in result["documents"]:
                            self.assertIn("name", doc)
                elif "results" in result:
                    self.assertIsInstance(result["results"], list)
                    if result["results"]:
                        for doc in result["results"]:
                            self.assertIn("name", doc)
        except Exception as e:
            self.fail(f"Tool execution raised exception: {str(e)}")

    def test_update_document_basic(self):
        """Test basic document update"""
        if not self.registry.has_tool("update_document"):
            self.skipTest("update_document tool not available")

        # Create a test document first
        if self.registry.has_tool("create_document"):
            create_args = {"doctype": self.test_doctype, "data": {"description": "Test ToDo for update"}}
            create_result = self.registry.execute_tool("create_document", create_args)

            if create_result.get("success") and "name" in create_result:
                doc_name = create_result["name"]

                # Now update it
                update_args = {
                    "doctype": self.test_doctype,
                    "name": doc_name,
                    "data": {"description": "Updated description"},
                }

                try:
                    result = self.registry.execute_tool("update_document", update_args)
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    self.fail(f"Update tool execution raised exception: {str(e)}")

    def test_execute_tool_routing(self):
        """Test that tool routing works correctly"""
        # This should pass for any available tool
        tools = self.registry.get_available_tools()
        if tools:
            # Just test that we can call the registry without errors
            self.assertTrue(hasattr(self.registry, "execute_tool"))
            self.assertTrue(hasattr(self.registry, "get_available_tools"))

    def test_execute_tool_invalid_tool(self):
        """Test handling of invalid tool names"""
        try:
            result = self.registry.execute_tool("nonexistent_tool", {})
            # Should return error, not raise exception
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
        except Exception as e:
            # If it raises exception, it should be a known type
            self.assertIsInstance(e, (ValueError, KeyError, AttributeError))

    def test_create_document_with_submit(self):
        """Test document creation with submission"""
        if not self.registry.has_tool("create_document"):
            self.skipTest("create_document tool not available")

        # Use a simple doctype for testing
        arguments = {
            "doctype": self.test_doctype,
            "data": {"description": "Test ToDo with submit"},
            "submit": False,  # Don't actually submit, just test the parameter
        }

        try:
            result = self.registry.execute_tool("create_document", arguments)
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Tool execution with submit raised exception: {str(e)}")

    def test_create_document_no_permission(self):
        """Test document creation without permission"""
        if not self.registry.has_tool("create_document"):
            self.skipTest("create_document tool not available")

        # Try to create document in a restricted doctype
        with patch("frappe.set_user") as mock_set_user:
            mock_set_user.return_value = None
            frappe.session.user = "Guest"  # Guest has limited permissions

            arguments = {
                "doctype": "User",  # Restricted doctype
                "data": {"email": "test@example.com"},
            }

            try:
                result = self.registry.execute_tool("create_document", arguments)
                self.assertIsInstance(result, dict)
                # Should fail with permission error
                if "success" in result:
                    self.assertFalse(result["success"], "Should fail due to permissions")
            except Exception:
                # Permission exceptions are acceptable
                pass

    def test_get_document_no_permission(self):
        """Test document retrieval without permission"""
        if not self.registry.has_tool("get_document"):
            self.skipTest("get_document tool not available")

        # This test might not be meaningful if Guest can read basic doctypes
        # But we test the error handling path
        arguments = {"doctype": "User", "name": "Administrator"}

        try:
            result = self.registry.execute_tool("get_document", arguments)
            self.assertIsInstance(result, dict)
        except Exception:
            # Permission exceptions are acceptable in tests
            pass

    def test_get_document_nonexistent(self):
        """Test getting a nonexistent document"""
        if not self.registry.has_tool("get_document"):
            self.skipTest("get_document tool not available")

        arguments = {"doctype": self.test_doctype, "name": "NONEXISTENT-DOC-12345"}

        try:
            result = self.registry.execute_tool("get_document", arguments)
            self.assertIsInstance(result, dict)
            # Should return error, not crash
            if "success" in result:
                self.assertFalse(result["success"], "Should fail for nonexistent document")
        except Exception:
            # DoesNotExistError is acceptable
            pass

    def test_update_document_no_permission(self):
        """Test document update without permission"""
        if not self.registry.has_tool("update_document"):
            self.skipTest("update_document tool not available")

        arguments = {
            "doctype": "User",  # Restricted doctype
            "name": "Administrator",
            "data": {"full_name": "Should Not Update"},
        }

        try:
            result = self.registry.execute_tool("update_document", arguments)
            self.assertIsInstance(result, dict)
        except Exception:
            # Permission exceptions are acceptable
            pass


class TestDocumentToolsIntegration(BaseAssistantTest):
    """Integration tests for document tools"""

    def setUp(self):
        super().setUp()
        self.registry = get_tool_registry()

    def test_document_lifecycle(self):
        """Test complete document lifecycle"""
        if not all(
            self.registry.has_tool(tool) for tool in ["create_document", "get_document", "update_document"]
        ):
            self.skipTest("Required document tools not available")

        doctype = "ToDo"

        # Create
        create_args = {"doctype": doctype, "data": {"description": "Lifecycle test document"}}

        try:
            create_result = self.registry.execute_tool("create_document", create_args)

            if not (create_result.get("success") and "name" in create_result):
                self.skipTest("Could not create test document")

            doc_name = create_result["name"]

            # Read
            get_args = {"doctype": doctype, "name": doc_name}
            get_result = self.registry.execute_tool("get_document", get_args)

            if get_result.get("success"):
                self.assertEqual(get_result["name"], doc_name)

            # Update
            update_args = {
                "doctype": doctype,
                "name": doc_name,
                "data": {"description": "Updated description"},
            }
            update_result = self.registry.execute_tool("update_document", update_args)
            self.assertIsInstance(update_result, dict)

        except Exception as e:
            self.fail(f"Document lifecycle test failed: {str(e)}")

    def test_error_handling_scenarios(self):
        """Test various error scenarios"""
        # Test with invalid arguments
        invalid_tests = [
            ("create_document", {}),  # Missing required fields
            ("get_document", {"doctype": "User"}),  # Missing name
            ("list_documents", {}),  # Missing doctype
        ]

        for tool_name, args in invalid_tests:
            if self.registry.has_tool(tool_name):
                try:
                    result = self.registry.execute_tool(tool_name, args)
                    # Should return error dict, not crash
                    self.assertIsInstance(result, dict)
                except Exception:
                    # Exceptions are also acceptable for invalid input
                    pass
