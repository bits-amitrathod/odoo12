{
    "name"          : "Execute Query",
    'version'       : '11.0.0.1',
    "author"        : "Benchmark IT Solutions",
    "category"      : "Report",
    "summary"       : "Execute query from database",
    "depends"       : [
        "base",
        "mail",
    ],
    "data"          : [
        "views/ms_query_view.xml",
        "security/ir.model.access.csv",
    ],
    "demo"          : [],
    "test"          : [],
    "images"        : [
                        "static/description/images/main_1.png",
                        "static/description/images/main_2.png",
                        "static/description/images/main_3.png",
    ],
    "qweb"          : [],
    "css"           : [],
    "application"   : True,
    "installable"   : True,
    "auto_install"  : False,
}