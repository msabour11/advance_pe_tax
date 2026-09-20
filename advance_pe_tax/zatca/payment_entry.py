import frappe
import base64
import qrcode
import io
from frappe.utils import now_datetime


def get_tlv(tag, value):
    value_bytes = str(value or "").encode("utf-8")
    return bytes([tag]) + bytes([len(value_bytes)]) + value_bytes


def generate_zatca_qr(doc, method=None):
    company = frappe.get_doc("Company", doc.company)

    seller_name = company.company_name or ""
    vat_number = company.tax_id or "300000000000003"
    timestamp = now_datetime().strftime("%Y-%m-%dT%H:%M:%SZ")
    total_amount = "{:.2f}".format(
        float(getattr(doc, "paid_amount_after_tax", None) or doc.paid_amount or 0)
    )
    vat_amount = "{:.2f}".format(
        float(getattr(doc, "total_taxes_and_charges", None) or 0)
    )

    tlv = (
        get_tlv(1, seller_name)
        + get_tlv(2, vat_number)
        + get_tlv(3, timestamp)
        + get_tlv(4, total_amount)
        + get_tlv(5, vat_amount)
    )

    b64_string = base64.b64encode(tlv).decode("utf-8")

    # Generate QR image
    qr = qrcode.make(b64_string)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"zatca_qr_{doc.name}.png"
    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": filename,
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "attached_to_field": "custom_zatca_qr",
            "content": buffer.read(),
            "is_private": 0,
        }
    )
    _file.save(ignore_permissions=True)

    doc.db_set("custom_zatca_qr", _file.file_url)


### jinja


@frappe.whitelist()
def get_zatca_phase_1_qr_for_payment(payment_entry):
    if isinstance(payment_entry, str):
        doc = frappe.get_doc("Payment Entry", payment_entry)
    else:
        doc = payment_entry

    company = frappe.get_doc("Company", doc.company)

    seller_name = company.company_name or ""
    vat_number = company.tax_id or "300000000000003"
    timestamp = now_datetime().strftime("%Y-%m-%dT%H:%M:%SZ")
    total_amount = "{:.2f}".format(
        float(getattr(doc, "paid_amount_after_tax", None) or doc.paid_amount or 0)
    )
    vat_amount = "{:.2f}".format(
        float(getattr(doc, "total_taxes_and_charges", None) or 0)
    )

    tlv = (
        get_tlv(1, seller_name)
        + get_tlv(2, vat_number)
        + get_tlv(3, timestamp)
        + get_tlv(4, total_amount)
        + get_tlv(5, vat_amount)
    )

    b64_string = base64.b64encode(tlv).decode("utf-8")

    qr = qrcode.make(b64_string)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
