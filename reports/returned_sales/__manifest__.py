# -*- coding: utf-8 -*-
{
    'name': "Returned Sales",
    'summary':"Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/returned_sales_report.xml',
        'report/returned_sales_report_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
