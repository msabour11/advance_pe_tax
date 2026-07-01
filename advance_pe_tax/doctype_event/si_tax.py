import frappe
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries


def calc_tax_after_advance(doc, method=None):
    """
    Calculates the total advance tax from linked Payment Entries and adjusts the Sales Invoice taxes.
    """
    advance_tax_total = 0

    for advance in doc.advances:
        if advance.reference_type == "Payment Entry":
            tax_amount = (
                frappe.db.get_value(
                    "Payment Entry", advance.reference_name, "total_taxes_and_charges"
                )
                or 0
            )
            advance_tax_total += tax_amount
    frappe.msgprint(
        f"Total Advance Tax from linked Payment Entries: {advance_tax_total}"
    )

    if not advance_tax_total:
        doc.custom_total_taxes = doc.total_taxes_and_charges
    if advance_tax_total < 0:
        doc.custom_total_taxes = doc.total_taxes_and_charges + advance_tax_total
    else:
        doc.custom_total_taxes = doc.total_taxes_and_charges - advance_tax_total


def apply_advance_tax_adjustment(doc, method=None):

    advance_tax_total = 0

    for advance in doc.advances:
        if advance.reference_type == "Payment Entry":

            tax_amount = (
                frappe.db.get_value(
                    "Payment Entry", advance.reference_name, "total_taxes_and_charges"
                )
                or 0
            )

            advance_tax_total += tax_amount

    if not advance_tax_total:
        return

    # Remove existing adjustment row
    doc.taxes = [
        row for row in doc.taxes if row.description != "Advance Tax Adjustment"
    ]

    doc.append(
        "taxes",
        {
            "charge_type": "Actual",
            "account_head": "ضريبة القيمة المضافة للمبيعات 15 % - Alassi",
            "description": "Advance Tax Adjustment",
            "tax_amount": -advance_tax_total,
        },
    )
    doc.run_method("calculate_taxes_and_totals")


def reverse_advance_tax_on_si_submit(doc, method):
    """
    Hooked to Sales Invoice 'on_submit'.
    Reverses advance taxes booked on associated Payment Entries proportionally.
    Handles both 'Deduct' and 'Add' tax types dynamically.
    """
    if not doc.advances:
        return

    gl_entries = []

    for adv in doc.advances:
        if adv.reference_type != "Payment Entry" or not adv.reference_name:
            continue

        # Load the original Payment Entry document
        pe = frappe.get_doc("Payment Entry", adv.reference_name)

        # 1. Map account heads to their respective tax type (Add or Deduct)
        tax_type_map = {}
        for tax_row in pe.get("taxes"):
            if tax_row.account_head:
                tax_type_map[tax_row.account_head] = tax_row.add_deduct_tax

        # 2. Fetch all GL entries for this Payment Entry (excluding the bank/cash row)
        tax_gl = frappe.db.get_all(
            "GL Entry",
            filters={
                "voucher_type": "Payment Entry",
                "voucher_no": pe.name,
                "is_cancelled": 0,
                "account": ("!=", pe.paid_to),
            },
            fields=["account", "debit", "credit", "cost_center"],
        )

        if not tax_gl:
            continue

        # Determine the base amount denominator for proportion calculation
        base = flt(pe.paid_amount) or flt(pe.received_amount)
        if not base:
            continue

        proportion = flt(adv.allocated_amount) / base
        posting_date = doc.posting_date or frappe.utils.today()

        for tax_row in tax_gl:
            tax_type = tax_type_map.get(tax_row.account, "Deduct")

            # Determine debits and credits based on Tax Type
            if tax_type == "Add":
                # Original entry credited the tax account. Reversal: Debit Tax, Credit Bank
                tax_amount = flt(tax_row.credit) * proportion
                if tax_amount <= 0:
                    continue

                bank_debit, bank_credit = 0, tax_amount
                tax_debit, tax_credit = tax_amount, 0
            else:
                # Original entry debited the tax account. Reversal: Debit Bank, Credit Tax
                tax_amount = flt(tax_row.debit) * proportion
                if tax_amount <= 0:
                    continue

                bank_debit, bank_credit = tax_amount, 0
                tax_debit, tax_credit = 0, tax_amount

            # 3. Append Bank Account entry (Party Type & Party stripped to avoid validation errors)
            gl_entries.append(
                doc.get_gl_dict(
                    {
                        "account": pe.paid_to,
                        "against": tax_row.account,
                        "debit": bank_debit,
                        "credit": bank_credit,
                        "posting_date": posting_date,
                        "against_voucher_type": "Sales Invoice",
                        "against_voucher": doc.name,
                        "cost_center": doc.cost_center or tax_row.cost_center,
                    }
                )
            )

            # 4. Append Tax Account entry
            gl_entries.append(
                doc.get_gl_dict(
                    {
                        "account": tax_row.account,
                        "against": pe.paid_to,
                        "debit": tax_debit,
                        "credit": tax_credit,
                        "posting_date": posting_date,
                        "against_voucher_type": "Sales Invoice",
                        "against_voucher": doc.name,
                        "cost_center": tax_row.cost_center,
                    }
                )
            )

    if gl_entries:
        make_gl_entries(gl_entries, cancel=0, update_outstanding="No")


def cancel_reversed_advance_tax_on_si_cancel(doc, method):

    frappe.db.sql(
        """
        UPDATE `tabGL Entry` 
        SET is_cancelled = 1, modified = %s, modified_by = %s 
        WHERE voucher_type = 'Sales Invoice' 
          AND voucher_no = %s 
          AND against_voucher_type = 'Sales Invoice'
          AND against_voucher = %s
          AND is_cancelled = 0
        """,
        (frappe.utils.now(), frappe.session.user, doc.name, doc.name),
    )
