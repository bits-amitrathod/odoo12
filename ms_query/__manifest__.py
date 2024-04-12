{
    "name"          : "Execute Query",
    "version"       : "1.0",
    "summary"       : "Execute query from database",
    "description"   : """
        Execute query without open postgres
Goto : Settings > Technical
    """,
    "depends"       : [
        "base",
        "mail",
    ],
    "data"          : [
        # "views/ms_query_view.xml",
        "security/ir.model.access.csv",
    ],
    "images"        : [
        "static/description/images/main_screenshot.png",
        "static/description/images/main_1.png",
        "static/description/images/main_2.png",
        "static/description/images/main_3.png",
    ],
    "application"   : True,
    "installable"   : True,
    "auto_install"  : False,
}
