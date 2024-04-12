# -*- coding: utf-8 -*-
{
    'name': "In Stock Report",
    'summary':"Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','stock','prioritization_engine','vendor_offer'],

    'qweb': ['static/src/xml/*.xml'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/in_stock_report.xml',
        # 'views/in_stock_report_print.xml',
        # 'views/in_stock_report_pdf.xml',
        # 'views/tree_view_asset.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
