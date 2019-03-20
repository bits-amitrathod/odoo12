# -*- coding: utf-8 -*-
{
    'name': "TPS Report",

    # 'summary': """""",
    #
    # 'description': """
    #      This module provides Sales Report Total Product sale.
    # """,

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','product','purchase','sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',

        'views/tps_report_view.xml',
        'report/selected_product_report.xml',
        'report/selected_product_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}