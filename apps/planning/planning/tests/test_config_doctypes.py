import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = ROOT / "mrp" / "doctype"


def load_doctype(folder, filename):
    return json.loads((DOCTYPE_ROOT / folder / filename).read_text())


def fieldnames(doctype_json):
    return {field["fieldname"] for field in doctype_json["fields"] if "fieldname" in field}


def permission_roles(doctype_json):
    return {permission["role"] for permission in doctype_json["permissions"]}


class TestConfigDocTypes(unittest.TestCase):
    def test_material_planning_parameter_fields_and_permissions(self):
        doc = load_doctype(
            "mrp_material_planning_parameter",
            "mrp_material_planning_parameter.json",
        )

        self.assertEqual(doc["name"], "MRP Material Planning Parameter")
        self.assertEqual(doc["module"], "MRP")
        self.assertTrue(
            {
                "item_code",
                "company",
                "warehouse",
                "supply_type",
                "planning_policy",
                "safety_stock",
                "reorder_level",
                "max_stock",
                "fixed_lot",
                "minimum_lot",
                "lot_multiple",
                "lead_time_days",
                "default_bom",
                "default_warehouse",
                "enabled",
            }.issubset(fieldnames(doc))
        )
        self.assertIn("MRP Data Administrator", permission_roles(doc))

    def test_element_config_fields_and_permissions(self):
        doc = load_doctype("mrp_element_config", "mrp_element_config.json")

        self.assertEqual(doc["name"], "MRP Element Config")
        self.assertTrue(
            {
                "source_doctype",
                "item_field",
                "company_field",
                "warehouse_field",
                "quantity_field",
                "date_field",
                "status_filters",
                "direction",
                "priority",
                "enabled",
                "exclusion_behavior",
            }.issubset(fieldnames(doc))
        )
        self.assertIn("MRP Data Administrator", permission_roles(doc))

    def test_filter_preset_fields(self):
        doc = load_doctype("mrp_filter_preset", "mrp_filter_preset.json")

        self.assertEqual(doc["name"], "MRP Filter Preset")
        self.assertTrue(
            {
                "company",
                "warehouse",
                "item_code",
                "item_group",
                "from_date",
                "to_date",
                "planning_policy",
            }.issubset(fieldnames(doc))
        )

    def test_settings_fields(self):
        doc = load_doctype("mrp_settings", "mrp_settings.json")

        self.assertEqual(doc["name"], "MRP Settings")
        self.assertEqual(doc["issingle"], 1)
        self.assertTrue(
            {
                "default_planning_horizon_days",
                "queue",
                "cleanup_unconfirmed_orders",
                "enable_production_plan_aggregation",
                "max_bom_depth",
                "max_bom_rows",
                "templates_initialized",
            }.issubset(fieldnames(doc))
        )


if __name__ == "__main__":
    unittest.main()
