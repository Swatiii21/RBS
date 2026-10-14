"""Services package initialization."""

from app.services.logging_service import log_activity, get_activity_logs, get_logger
from app.services.settings_service import get_setting, update_setting, update_settings_batch, get_grouped_settings
from app.services.menu_service import get_menu_items, get_menu_item_by_id, create_menu_item, update_menu_item, deactivate_menu_item, delete_menu_item
from app.services.billing_service import calculate_billing_breakdown, finalize_order_and_generate_invoice, get_invoice_by_number, get_invoices_history
from app.services.order_service import create_order, add_item_to_order, update_order_item_quantity, remove_order_item, update_order_discount, cancel_order, get_order_by_id, get_orders, get_order_items
from app.services.quality_service import get_defects, create_defect, update_defect_status, calculate_pareto_analysis, get_fmea_records, add_fmea_record, get_fishbone_causes, get_pdca_cycles, get_quality_summary_metrics

__all__ = [
    "log_activity", "get_activity_logs", "get_logger",
    "get_setting", "update_setting", "update_settings_batch", "get_grouped_settings",
    "get_menu_items", "get_menu_item_by_id", "create_menu_item", "update_menu_item", "deactivate_menu_item", "delete_menu_item",
    "calculate_billing_breakdown", "finalize_order_and_generate_invoice", "get_invoice_by_number", "get_invoices_history",
    "create_order", "add_item_to_order", "update_order_item_quantity", "remove_order_item", "update_order_discount", "cancel_order", "get_order_by_id", "get_orders", "get_order_items",
    "get_defects", "create_defect", "update_defect_status", "calculate_pareto_analysis", "get_fmea_records", "add_fmea_record", "get_fishbone_causes", "get_pdca_cycles", "get_quality_summary_metrics",
]
