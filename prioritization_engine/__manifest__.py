# -*- coding: utf-8 -*-
{
    'name': " STOCKHAWK ",
    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sale',
    'version': '16.14',

    # any module necessary for this one to work correctly

    'depends': ['base','sale', 'sales_team', 'purchase','product','product_brand','sale_management','stock','web_one2many_selectable','account'],

    # always loaded
    'data': [
        'security/res_user_prioritization.xml',
        'security/ir.model.access.csv',
        'views/email_template.xml',
        'views/res_config_setting_view.xml',
        'views/saleorder_views.xml',
        'views/report_invoice.xml',
        'views/prioritization_views.xml',
        # 'views/web_assets.xml',  Added using assets
        # 'views/templates.xml',
        'views/prioritization_schedular_views.xml',
        'views/release_product_quantity_scheduler_views.xml',
        'views/process_high_priority_requests.xml',
        'data/sales_team_data_prioritization.xml',
    ],

    # 'assets': {
    #     'web.assets_backend': [
    #         'prioritization_engine/static/src/js/prioritization_engine.js',
    #     ],
    # },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'auto-install': True,
    'installable': True,
}
