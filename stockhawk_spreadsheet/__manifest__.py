# -*- coding: utf-8 -*-
{
    'name': "Stockhawk Spreadsheet",
    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'version': '1.0',
    'category': 'Productivity/Documents',
    'summary': 'Stockhawk Spreadsheet',
    'description': 'Stockhawk Spreadsheet',

    # any module necessary for this one to work correctly
    'depends': ['website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stockhawk_submission.xml',
        # 'views/views.xml',
        'views/stockhawk_spreadsheet.xml',
    ],

    'application': False,
    'installable': True,
    'auto_install': True,
}
