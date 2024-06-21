# -*- coding: utf-8 -*-
{
    'name': "Customize Sales Order",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'delivery', 'prioritization_engine', 'purchase','account_reports'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/mail_template_data_cstm.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',

}