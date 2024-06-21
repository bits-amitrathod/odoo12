# -*- coding: utf-8 -*-
{
    'name': "Receiving List",
    'summary': "Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'purchase', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'report/receiving_list_report.xml',
        # 'report/receiving_list_report_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}