# -*- coding: utf-8 -*-
{
    'name': "SPS Receiving List",

    'summary': """
      Report
       """,

    'description': """

    """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '1.0',

    'depends': ['base', 'stock', 'stock_barcode', 'delivery'],

    'data': [
        'security/ir.model.access.csv',
        'views/stock_barcode_templates.xml',
        'views/views.xml',
        'reports/sps_receiving_list.xml'
    ],
    'qweb': [
        'views/qweb_templates.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}