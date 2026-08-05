# # Copyright (c) 2026, Mohamed AbdElsabour and contributors
# # For license information, please see license.txt

# import frappe


# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data


# def get_columns():
#     return [
#         {
#             "fieldname": "invoice",
#             "label": "Invoice",
#             "fieldtype": "Link",
#             "options": "Sales Invoice",
#             "width": 150,
#         },
#         {
#             "fieldname": "customer",
#             "label": "Customer",
#             "fieldtype": "Link",
#             "options": "Customer",
#             "width": 150,
#         },
#         {
#             "fieldname": "total",
#             "label": "Total",
#             "fieldtype": "Currency",
#             "options": "currency",
#             "width": 120,
#         },
#         {
#             "fieldname": "total_taxes",
#             "label": "Total Taxes",
#             "fieldtype": "Currency",
#             "options": "currency",
#             "width": 120,
#         },
#         {
#             "fieldname": "grand_total",
#             "label": "Grand Total",
#             "fieldtype": "Currency",
#             "options": "currency",
#             "width": 120,
#         },
#         {
#             "fieldname": "advance_payment",
#             "label": "Advance Payment",
#             "fieldtype": "Currency",
#             "options": "currency",
#             "width": 130,
#         },
#         {
#             "fieldname": "retention_total",
#             "label": "Retention Total",
#             "fieldtype": "Currency",
#             "options": "currency",
#             "width": 130,
#         },
#         {
#             "fieldname": "currency",
#             "label": "Currency",
#             "fieldtype": "Data",
#             "hidden": 1,
#         },
#     ]


# def get_data(filters):
#     conditions = get_conditions(filters)

#     # Using a subquery for the child table sum ensures we don't get duplicate rows
#     # if there are multiple retention rows per invoice.
#     sql = """
#         SELECT
#             si.name AS invoice,
#             si.customer,
#             si.total,
#             si.total_taxes_and_charges AS total_taxes,
#             si.grand_total,
#             si.total_advance AS advance_payment,
#             si.currency,
#             COALESCE((
#                 SELECT SUM(total)
#                 FROM `tabSales Invoice Retention`
#                 WHERE parent = si.name
#             ), 0) AS retention_total
#         FROM
#             `tabSales Invoice` si
#         WHERE
#             si.docstatus = 1
#             {conditions}
#         ORDER BY
#             si.posting_date DESC
#     """.format(conditions=conditions)

#     return frappe.db.sql(sql, filters, as_dict=True)


# def get_conditions(filters):
#     conditions = ""

#     if filters.get("company"):
#         conditions += " AND si.company = %(company)s"

#     if filters.get("from_date"):
#         conditions += " AND si.posting_date >= %(from_date)s"

#     if filters.get("to_date"):
#         conditions += " AND si.posting_date <= %(to_date)s"

#     if filters.get("customer"):
#         conditions += " AND si.customer = %(customer)s"

#     if filters.get("invoice"):
#         conditions += " AND si.name = %(invoice)s"

#     return conditions


############################ ki with date
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Invoice"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 180,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Total"),
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Total Taxes"),
            "fieldname": "total_taxes_and_charges",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Advance Paid"),
            "fieldname": "total_advance",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Retention Total"),
            "fieldname": "retention_total",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Outstanding Amount"),
            "fieldname": "outstanding_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    query = """
        SELECT
            si.name,
            si.customer,
            si.company,
            si.posting_date,
            si.total,
            si.total_taxes_and_charges,
            si.grand_total,
            si.total_advance,
            COALESCE(SUM(sir.total), 0) AS retention_total,
            si.outstanding_amount,
            si.status
        FROM
            `tabSales Invoice` si
        LEFT JOIN
            `tabSales Invoice Retention` sir ON sir.parent = si.name AND sir.parenttype = 'Sales Invoice'
        WHERE
            si.docstatus = 1
            {conditions}
        GROUP BY
            si.name
        ORDER BY
            si.posting_date DESC, si.name DESC
    """.format(conditions=conditions)

    data = frappe.db.sql(query, filters, as_dict=1)
    return data


def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND si.company = %(company)s"

    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"

    if filters.get("invoice"):
        conditions += " AND si.name = %(invoice)s"

    if filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"

    if filters.get("status"):
        conditions += " AND si.status = %(status)s"

    if filters.get("docstatus") is not None:
        conditions += " AND si.docstatus = %(docstatus)s"
    else:
        # Default: show submitted and draft, exclude cancelled
        conditions += " AND si.docstatus IN (0, 1)"

    return conditions
