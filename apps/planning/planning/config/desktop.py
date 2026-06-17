from frappe import _


def get_data():
	return [
		{
			"module_name": "MPS",
			"color": "blue",
			"icon": "octicon octicon-calendar",
			"type": "module",
			"label": _("MPS"),
		},
		{
			"module_name": "MRP",
			"color": "grey",
			"icon": "octicon octicon-package",
			"type": "module",
			"label": _("MRP"),
		},
		{
			"module_name": "APS",
			"color": "orange",
			"icon": "octicon octicon-graph",
			"type": "module",
			"label": _("APS"),
		},
	]
