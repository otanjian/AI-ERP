app_name = "planning"
app_title = "Planning"
app_publisher = "Bosofts"
app_description = "Third-party Planning and MRP app for ERPNext v16"
app_email = "support@example.com"
app_license = "mit"
app_icon = "octicon octicon-graph"
app_color = "#4F46E5"
app_logo_url = "/assets/planning/images/planning-logo.svg"

add_to_apps_screen = [
	{
		"name": "planning",
		"logo": "/assets/planning/images/planning-logo.svg",
		"title": "Planning",
		"route": "/app/计划管理",
		"has_permission": "planning.permissions.has_app_permission",
	}
]

fixtures = [
    {"dt": "Module Def", "filters": [["name", "in", ["MPS", "MRP", "APS"]]]},
    {
        "dt": "Role",
        "filters": [
            [
                "name",
                "in",
                [
                    "MRP Planner",
                    "MRP Supervisor",
                    "MRP Data Administrator",
                    "Planning System Administrator",
                ],
            ]
        ],
    },
    {"dt": "Workspace", "filters": [["name", "=", "计划管理"]]},
]
