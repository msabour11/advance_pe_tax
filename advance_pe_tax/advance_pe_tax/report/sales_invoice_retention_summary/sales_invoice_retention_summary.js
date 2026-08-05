// Copyright (c) 2026, Mohamed AbdElsabour and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Invoice Retention Summary"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 0,
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			reqd: 0,
		},
		{
			fieldname: "invoice",
			label: __("Invoice"),
			fieldtype: "Link",
			options: "Sales Invoice",
			reqd: 0,
			get_query: function () {
				return {
					filters: {
						docstatus: ["in", [0, 1]],
					},
				};
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 0,
		},
		// {
		// 	fieldname: "status",
		// 	label: __("Status"),
		// 	fieldtype: "Select",
		// 	options:
		// 		"\nDraft\nReturn\nCredit Note Issued\nSubmitted\nPaid\nPartly Paid\nUnpaid\nOverdue\nCancelled\nInternal Transfer",
		// 	reqd: 0,
		// },
		// {
		// 	fieldname: "docstatus",
		// 	label: __("Document Status"),
		// 	fieldtype: "Select",
		// 	options: "\n0\n1\n2",
		// 	default: "",
		// 	reqd: 0,
		// },
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "status" && data) {
			if (data.status === "Paid") {
				value = `<span style="color: green; font-weight: bold;">${value}</span>`;
			} else if (data.status === "Overdue") {
				value = `<span style="color: red; font-weight: bold;">${value}</span>`;
			} else if (data.status === "Unpaid") {
				value = `<span style="color: orange; font-weight: bold;">${value}</span>`;
			} else if (data.status === "Partly Paid") {
				value = `<span style="color: blue; font-weight: bold;">${value}</span>`;
			} else if (data.status === "Draft") {
				value = `<span style="color: gray;">${value}</span>`;
			} else if (data.status === "Cancelled") {
				value = `<span style="color: darkred; text-decoration: line-through;">${value}</span>`;
			}
		}

		if (column.fieldname == "outstanding_amount" && data && data.outstanding_amount > 0) {
			value = `<span style="color: red;">${value}</span>`;
		}

		return value;
	},
};
