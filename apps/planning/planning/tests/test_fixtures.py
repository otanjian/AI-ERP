import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name):
    return json.loads((ROOT / "fixtures" / name).read_text())


class TestFixtures(unittest.TestCase):
    def test_workspace_contains_required_planning_groups(self):
        workspace = load_fixture("workspace.json")[0]
        self.assertEqual(workspace["doctype"], "Workspace")
        self.assertEqual(workspace["name"], "计划管理")
        content = json.dumps(workspace, ensure_ascii=False)

        for label in [
            "计划总览",
            "MPS 主生产计划",
            "MRP 物料需求计划",
            "APS 高级计划排程",
            "计划设置",
        ]:
            self.assertIn(label, content)

    def test_mps_and_aps_are_placeholders(self):
        workspace = load_fixture("workspace.json")[0]
        content = json.dumps(workspace, ensure_ascii=False)

        self.assertIn("MPS 工作台（站位）", content)
        self.assertIn("APS 工作台（站位）", content)

    def test_roles_fixture_declares_planning_roles(self):
        roles = {row["role_name"] for row in load_fixture("role.json")}

        self.assertEqual(
            roles,
            {
                "MRP Planner",
                "MRP Supervisor",
                "MRP Data Administrator",
                "Planning System Administrator",
            },
        )


if __name__ == "__main__":
    unittest.main()
