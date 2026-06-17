import unittest

from planning.mrp.element_templates import get_default_element_templates


class TestElementTemplates(unittest.TestCase):
    def test_default_templates_cover_erpnext_v16_sources(self):
        templates = {template["element_name"]: template for template in get_default_element_templates()}

        self.assertIn("Sales Order Item Demand", templates)
        self.assertIn("Bin Actual Quantity Supply", templates)
        self.assertIn("Purchase Order Item Supply", templates)
        self.assertIn("Material Request Item Weak Supply", templates)
        self.assertIn("Work Order Supply", templates)
        self.assertIn("Work Order Item Component Demand", templates)

    def test_bin_template_uses_actual_qty_not_projected_qty(self):
        templates = {template["element_name"]: template for template in get_default_element_templates()}
        bin_template = templates["Bin Actual Quantity Supply"]

        self.assertEqual(bin_template["source_doctype"], "Bin")
        self.assertEqual(bin_template["quantity_field"], "actual_qty")
        self.assertNotEqual(bin_template["quantity_field"], "projected_qty")

    def test_material_request_supply_is_optional_and_lower_priority(self):
        templates = {template["element_name"]: template for template in get_default_element_templates()}
        material_request = templates["Material Request Item Weak Supply"]
        purchase_order = templates["Purchase Order Item Supply"]

        self.assertFalse(material_request["enabled"])
        self.assertGreater(material_request["priority"], purchase_order["priority"])

    def test_work_order_item_uses_parent_date_hint(self):
        templates = {template["element_name"]: template for template in get_default_element_templates()}
        component_demand = templates["Work Order Item Component Demand"]

        self.assertEqual(component_demand["source_doctype"], "Work Order Item")
        self.assertEqual(component_demand["date_source"], "parent_work_order")


if __name__ == "__main__":
    unittest.main()
