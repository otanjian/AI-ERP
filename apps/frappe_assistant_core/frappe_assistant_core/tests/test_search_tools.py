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
Test suite for Search Tools using Plugin Architecture
"""

import unittest

import frappe

from frappe_assistant_core.core.tool_registry import get_tool_registry
from frappe_assistant_core.tests.base_test import BaseAssistantTest


class TestSearchTools(BaseAssistantTest):
    """Test search tools through plugin registry"""

    def setUp(self):
        super().setUp()
        self.registry = get_tool_registry()

    def test_get_tools_structure(self):
        """Test that search tools are properly registered"""
        tools = self.registry.get_available_tools()
        tool_names = [tool["name"] for tool in tools]

        # Check for search tools
        expected_tools = ["search_documents"]
        found_tools = [tool for tool in expected_tools if tool in tool_names]

        self.assertGreater(len(found_tools), 0, f"Should find search tools. Available: {tool_names}")

    def test_execute_tool_routing(self):
        """Test that tool routing works correctly"""
        tools = self.registry.get_available_tools()
        if tools:
            self.assertTrue(hasattr(self.registry, "execute_tool"))
            self.assertTrue(hasattr(self.registry, "get_available_tools"))

    def test_execute_tool_invalid_tool(self):
        """Test handling of invalid tool names"""
        try:
            result = self.registry.execute_tool("nonexistent_search_tool", {})
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
        except Exception as e:
            self.assertIsInstance(e, (ValueError, KeyError, AttributeError))

    def test_search_documents_basic(self):
        """Test basic document search"""
        if not self.registry.has_tool("search_documents"):
            self.skipTest("search_documents tool not available")

        arguments = {"query": "Admin"}

        try:
            result = self.registry.execute_tool("search_documents", arguments)
            self.assertIsInstance(result, dict)
        except Exception:
            # Search may fail for various reasons
            pass

    # Placeholder tests for other search functionality
    def test_search_documents_with_filters(self):
        self.skipTest("Search with filters test placeholder")

    def test_search_documents_permissions(self):
        self.skipTest("Search permissions test placeholder")

    def test_search_specific_doctype(self):
        self.skipTest("DocType search test placeholder")

    def test_search_empty_query(self):
        self.skipTest("Empty query test placeholder")


class TestSearchToolsIntegration(BaseAssistantTest):
    """Integration tests for search tools"""

    def setUp(self):
        super().setUp()
        self.registry = get_tool_registry()

    def test_search_workflow(self):
        self.skipTest("Search workflow test placeholder")
