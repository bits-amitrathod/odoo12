# -*- coding: utf-8 -*-
{
    'name': "Pick Report",

    'author': "Benchmark IT Solutions (I) Pvt. Ltd",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/views.xml',
        'report/pick_report.xml',
        'report/pick_report_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}