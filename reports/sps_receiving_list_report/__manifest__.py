# -*- coding: utf-8 -*-
{
    'name': "SPS Receiving List",

    'summary': """
       """,

    'description': """
        
    """,

    'author': "Benchmark It Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '1.0',

    'depends': ['base','stock','stock_barcode', 'delivery','product_expiry_extension'],

    'data': [
        'views/views.xml',
        'reports/sps_receiving_list.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}