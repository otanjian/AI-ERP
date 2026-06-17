from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil


@dataclass(frozen=True)
class PlanningParameter:
    item_code: str
    company: str
    warehouse: str | None = None
    supply_type: str = "BUY"
    lead_time_days: int = 0
    safety_stock: float = 0
    reorder_level: float = 0
    max_stock: float = 0
    fixed_lot: float | None = None
    minimum_lot: float | None = None
    lot_multiple: float | None = None
    default_bom: str | None = None
    default_warehouse: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class Snapshot:
    item_code: str
    company: str
    warehouse: str | None
    planning_date: date
    quantity: float
    priority: int = 100


@dataclass(frozen=True)
class PlannedOrder:
    item_code: str
    company: str
    warehouse: str | None
    supply_type: str
    quantity: float
    requirement_date: date
    order_date: date
    downstream_doctype: str | None = None
    downstream_document: str | None = None


def select_parameter(
    parameters: list[PlanningParameter],
    item_code: str,
    company: str,
    warehouse: str | None = None,
) -> PlanningParameter | None:
    matches = [
        parameter
        for parameter in parameters
        if parameter.enabled
        and parameter.item_code == item_code
        and parameter.company == company
        and parameter.warehouse in {warehouse, None}
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda parameter: parameter.warehouse is None)[0]


def stock_supply_quantity(bin_row: dict) -> float:
    return float(bin_row.get("actual_qty") or 0)


def apply_lot_rules(
    quantity: float,
    fixed_lot: float | None = None,
    minimum_lot: float | None = None,
    lot_multiple: float | None = None,
) -> float:
    if fixed_lot:
        return fixed_lot

    planned_quantity = quantity

    if minimum_lot:
        planned_quantity = max(planned_quantity, minimum_lot)

    if lot_multiple:
        planned_quantity = ceil(planned_quantity / lot_multiple) * lot_multiple

    return planned_quantity


def calculate_order_date(requirement_date: date, lead_time_days: int = 0) -> date:
    return requirement_date - timedelta(days=lead_time_days or 0)


def is_confirmation_idempotent(planned_order: PlannedOrder) -> bool:
    return bool(planned_order.downstream_doctype and planned_order.downstream_document)
