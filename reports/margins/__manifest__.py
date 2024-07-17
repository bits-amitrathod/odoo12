# -*- coding: utf-8 -*-
{
    'name': "Margins",
    'summary':"Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','sale', 'sale_margin', 'product_margin', 'prioritization_engine'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/margins_report.xml',
        'report/margins_report_template.xml',
        'report/margins_report_by_cust_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
