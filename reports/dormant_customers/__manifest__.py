# -*- coding: utf-8 -*-
{
    'name': "Dormant Customers",
    'summary':'Report',
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'category': 'report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'report/dormant_customers_report.xml',
        # 'report/dormant_customers_report_template.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
