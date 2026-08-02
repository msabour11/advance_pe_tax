frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {},
});

frappe.ui.form.on("Sales Invoice Advance", {
	custom_percentage: function (frm, cdt, cdn) {
		fetch_payment_entry(frm, cdt, cdn);
	},

	allocated_amount: function (frm, cdt, cdn) {
		set_allocated_vat_amount(frm, cdt, cdn);
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
			const allocated_amount = row.advance_amount * (row.custom_percentage / 100);

			let allocated_vat = 0;
			if (row.custom_percentage > 0 && allocated_amount > 0) {
				allocated_vat = (allocated_amount * 0.15) / 1.15; // Assuming 15% VAT rate, adjust as necessary
			}

			// 3. Calculate the Allocated Amount

			// 4. Set all values simultaneously (this automatically refreshes the table row)
			frappe.model.set_value(cdt, cdn, {
				custom_advance_vat: advance_vat,
				custom_allocated_vat: allocated_vat,
				allocated_amount: allocated_amount,
			});
		});
	}
}

function set_allocated_vat_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];

	let allocated_vat = 0;
	if (row.allocated_amount > 0) {
		allocated_vat = (row.allocated_amount * 0.15) / 1.15; // Assuming 15% VAT rate, adjust as necessary
	}

	// Set the Allocated VAT value
	frappe.model.set_value(cdt, cdn, "custom_allocated_vat", allocated_vat);
}
