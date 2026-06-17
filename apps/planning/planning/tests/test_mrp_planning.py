import unittest
from datetime import date

from planning.mrp.planning import (
    PlannedOrder,
    PlanningParameter,
    apply_lot_rules,
    calculate_order_date,
    is_confirmation_idempotent,
    select_parameter,
    stock_supply_quantity,
)


class TestMRPPlanning(unittest.TestCase):
    def test_warehouse_specific_parameter_wins(self):
        broad = PlanningParameter(
            item_code="ITEM-001",
            company="Bosofts",
            warehouse=None,
            supply_type="BUY",
            lead_time_days=5,
        )
        specific = PlanningParameter(
            item_code="ITEM-001",
            company="Bosofts",
            warehouse="Stores - B",
            supply_type="MAKE",
            lead_time_days=2,
        )

        selected = select_parameter([broad, specific], "ITEM-001", "Bosofts", "Stores - B")

        self.assertEqual(selected, specific)

    def test_default_stock_supply_uses_actual_qty(self):
        quantity = stock_supply_quantity({"actual_qty": 12, "projected_qty": 99})

        self.assertEqual(quantity, 12)

    def test_lot_rules_apply_minimum_and_multiple(self):
        quantity = apply_lot_rules(11, minimum_lot=20, lot_multiple=12)

        self.assertEqual(quantity, 24)

    def test_fixed_lot_overrides_requirement_quantity(self):
        quantity = apply_lot_rules(11, fixed_lot=50, minimum_lot=20, lot_multiple=12)

        self.assertEqual(quantity, 50)

    def test_lead_time_offsets_order_date(self):
        order_date = calculate_order_date(date(2026, 6, 20), 5)

        self.assertEqual(order_date, date(2026, 6, 15))

    def test_existing_downstream_reference_is_idempotent(self):
        planned_order = PlannedOrder(
            item_code="ITEM-001",
            company="Bosofts",
            warehouse="Stores - B",
            supply_type="BUY",
            quantity=10,
            requirement_date=date(2026, 6, 20),
            order_date=date(2026, 6, 15),
            downstream_doctype="Material Request",
            downstream_document="MAT-MR-0001",
        )

        self.assertTrue(is_confirmation_idempotent(planned_order))


if __name__ == "__main__":
    unittest.main()
