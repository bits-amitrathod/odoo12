# -*- coding: utf-8 -*-
{
    'name': "Returned Sales",

    'author': "Benchmark IT Solutions (I) Pvt Ltd",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'sale'],

    'data': [
        'views/views.xml',
        'report/returned_sales_report.xml',
        'report/returned_sales_report_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}