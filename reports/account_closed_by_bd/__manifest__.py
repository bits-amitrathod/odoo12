# -*- coding: utf-8 -*-
{
    'name': "Account Closed in 12 Months by Business Development",

    'summary': """
      Report
       """,

    'description': """

    """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/account_closed_by_bd_report.xml',
        'report/account_closed_by_bd_temp.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
