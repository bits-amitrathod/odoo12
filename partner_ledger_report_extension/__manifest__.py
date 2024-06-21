# -*- coding: utf-8 -*-
{
    'name': "Partner Ledger Report Extension",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_reports'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml'
    ],

    'application': True,
    'auto-install': False,
    'installable': True,
}
