import frappe
from frappe.utils import flt


@frappe.whitelist()
def create_advance_invoice(source_name, item_code, amount):
    # Fetch the parent Sales Order
    so = frappe.get_doc("Sales Order", source_name)

    # Initialize a new Sales Invoice
    si = frappe.new_doc("Sales Invoice")
    si.customer = so.customer
    si.company = so.company
    si.currency = so.currency
    si.conversion_rate = so.conversion_rate

    # Set your custom flag
    # si.custom_advance_invoice = 1

    # Append the selected non-stock item
    si.append(
        "items",
        {
            "item_code": item_code,
            "qty": 1,
            "rate": flt(amount),
            "sales_order": so.name,  # Links the invoice back to the SO
        },
    )

    si.taxes_and_charges = so.taxes_and_charges  # Copy taxes and charges from SO
    si.run_method("calculate_taxes_and_totals")  # Ensure all required fields are set

    # Auto-fetch default accounts, taxes, and other required fields
    si.set_missing_values()

    # Save the document (leaving it in Draft state for review)
    si.insert(ignore_permissions=True)

    return si.name


########333 kimi
import frappe
from frappe.utils import flt


@frappe.whitelist()
def create_advance_payment_invoice(
    sales_order,
    item_code,
    item_name,
    description,
    advance_amount,
    uom,
    income_account=None,
):
    """
    Create a Sales Invoice for advance payment from a Sales Order.
    Item is selected from Item master (non-stock items only).
    """

    # Validate Sales Order
    so = frappe.get_doc("Sales Order", sales_order)
    if so.docstatus != 1:
        frappe.throw(_("Sales Order must be submitted"))

    # Validate item is non-stock
    item = frappe.get_doc("Item", item_code)
    if item.is_stock_item:
        frappe.throw(_("Selected item must be a non-stock (service) item"))

    # Validate advance amount
    advance_amount = flt(advance_amount)
    if advance_amount <= 0:
        frappe.throw(_("Advance amount must be greater than zero"))

    # Get default income account if not provided
    item = frappe.get_doc("Item", item_code)
    income_account = None

    for d in item.item_defaults:
        if d.company == so.company and d.income_account:
            income_account = d.income_account
            break

    if not income_account:
        income_account = frappe.db.get_value(
            "Company", so.company, "default_income_account"
        )

    # Create Sales Invoice
    si = frappe.new_doc("Sales Invoice")
    si.customer = so.customer
    si.company = so.company
    si.currency = so.currency
    si.conversion_rate = so.conversion_rate
    si.selling_price_list = so.selling_price_list
    si.price_list_currency = so.price_list_currency
    si.plc_conversion_rate = so.plc_conversion_rate
    si.territory = so.territory
    si.customer_group = so.customer_group
    si.due_date = frappe.utils.nowdate()
    si.is_pos = 0
    si.remarks = f"Advance Payment for Sales Order {so.name}"

    # Set custom flag
    si.custom_advance_invoice = 1

    # Add the selected item from Item master
    si.append(
        "items",
        {
            "item_code": item_code,
            "item_name": item_name or item.item_name,
            "description": description or f"Advance Payment for {so.name}",
            "qty": 1,
            "rate": advance_amount,
            "amount": advance_amount,
            "uom": uom or item.stock_uom or "Nos",
            "sales_order": so.name,
            "income_account": income_account,
            "is_stock_item": 0,
        },
    )

    si.taxes_and_charges = so.taxes_and_charges  # Copy taxes and charges from SO

    # Set missing values and calculate
    si.set_missing_values()
    si.calculate_taxes_and_totals()

    # Insert and submit
    si.insert()
    # si.submit()

    # Create comment on Sales Order
    frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Sales Order",
            "reference_name": so.name,
            "content": f"Advance Invoice <a href='/app/sales-invoice/{si.name}'>{si.name}</a> created for amount {advance_amount}",
        }
    ).insert(ignore_permissions=True)

    return si.name
