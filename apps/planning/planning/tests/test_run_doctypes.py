import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = ROOT / "mrp" / "doctype"


def load_doctype(folder, filename):
    return json.loads((DOCTYPE_ROOT / folder / filename).read_text())


def fieldnames(doctype_json):
    return {field["fieldname"] for field in doctype_json["fields"] if "fieldname" in field}


class TestRunDocTypes(unittest.TestCase):
    def test_mrp_run_fields(self):
        doc = load_doctype("mrp_run", "mrp_run.json")

        self.assertEqual(doc["name"], "MRP Run")
        self.assertTrue(
            {
                "company",
                "from_date",
                "to_date",
                "status",
                "progress",
                "total_snapshots",
                "total_planned_orders",
                "error_message",
            }.issubset(fieldnames(doc))
        )

    def test_mrp_element_snapshot_fields(self):
        doc = load_doctype("mrp_element_snapshot", "mrp_element_snapshot.json")

        self.assertEqual(doc["name"], "MRP Element Snapshot")
        self.assertTrue(
            {
                "mrp_run",
                "source_doctype",
                "source_document",
                "source_row",
                "item_code",
                "company",
                "warehouse",
                "planning_date",
                "normalized_quantity",
                "original_quantity",
                "source_status",
                "priority",
                "metadata_json",
            }.issubset(fieldnames(doc))
        )

    def test_mrp_job_log_fields(self):
        doc = load_doctype("mrp_job_log", "mrp_job_log.json")

        self.assertEqual(doc["name"], "MRP Job Log")
        self.assertTrue(
            {
                "reference_doctype",
                "reference_name",
                "job_type",
                "status",
                "progress",
                "started_at",
                "ended_at",
                "result_counts",
                "warning_message",
                "error_message",
            }.issubset(fieldnames(doc))
        )


if __name__ == "__main__":
    unittest.main()
