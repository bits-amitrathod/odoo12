# -*- coding: utf-8 -*-
{
    'name': "Products on Order",
    'summary':"Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/products_on_order_report.xml',
        'report/products_on_order_report_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
