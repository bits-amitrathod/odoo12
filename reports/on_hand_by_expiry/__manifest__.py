# -*- coding: utf-8 -*-
{
    'name': "On Hand By Expiration",

    'author': "Benchmark IT Solutions (I) Pvt. Ltd",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'views/views.xml',
        'report/on_hand_by_expiration_report.xml',
        'report/on_hand_by_expiration_report_template.xml'
    ],
}