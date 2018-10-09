# -*- coding: utf-8 -*-
{
    'name': "On Hand By Date",

    'author': "Benchmark IT Solutions (I) Pvt. Ltd",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'views/views.xml',
        'report/on_hand_by_date_report.xml',
        'report/on_hand_by_date_report_template.xml'
    ],
}