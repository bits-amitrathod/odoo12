# -*- coding: utf-8 -*-
{
    'name': "Products on Order",
    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        'views/views.xml',
        'report/products_on_order_report.xml',
        'report/products_on_order_report_template.xml'
    ],

}