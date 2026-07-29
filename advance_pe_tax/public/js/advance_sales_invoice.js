frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {},
});

frappe.ui.form.on("Sales Invoice Advance", {
	custom_percentage: function (frm, cdt, cdn) {
		fetch_payment_entry(frm, cdt, cdn);
	},
});

function fetch_payment_entry(frm, cdt, cdn) {
	frappe.msgprint("Fetching Payment Entry details...");
	const row = locals[cdt][cdn];

	if (row.reference_type === "Payment Entry" && row.reference_name) {
		frappe.db.get_doc("Payment Entry", row.reference_name).then((payment_entry) => {
			// 1. Get the VAT from the Payment Entry
			const advance_vat = payment_entry.total_taxes_and_charges || 0;

			// 2. Calculate the Allocated VAT based on your formula
			// (Added a safeguard to prevent division by zero errors if percentage is 0)
			let allocated_vat = 0;
			if (row.custom_percentage > 0) {
				allocated_vat = advance_vat * (row.custom_percentage / 100);
			}

			// 3. Calculate the Allocated Amount
			const allocated_amount = row.advance_amount * (row.custom_percentage / 100);

			// 4. Set all values simultaneously (this automatically refreshes the table row)
			frappe.model.set_value(cdt, cdn, {
				custom_advance_vat: advance_vat,
				custom_allocated_vat: allocated_vat,
				allocated_amount: allocated_amount,
			});
		});
	}
}
