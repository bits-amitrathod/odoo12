# -*- coding: utf-8 -*-
{
    'name': "Sales By Count",

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'report/sales_by_count_report.xml',
        'report/sales_by_count_report_template.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}