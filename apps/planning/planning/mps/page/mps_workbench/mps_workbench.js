frappe.pages["mps-workbench"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("MPS Workbench"),
		single_column: true,
	});

	$(wrapper)
		.find(".layout-main-section")
		.html(
			`<div class="text-muted">${__(
				"MPS module is reserved for future development."
			)}</div>`
		);

	page.set_indicator(__("Placeholder"), "orange");
};
