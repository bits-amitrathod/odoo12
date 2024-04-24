# -*- coding: utf-8 -*-
{
    'name': "eCommerce CSTM",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'sequence': 59,
    'category': 'e-commerce',
    'version': '1.0',
    'depends': ['website_sale','payment_aquirer_cstm','vendor_offer'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data_views.xml',
        'views/quote_my_report.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sales/static/src/js/quote_my_report.js',
        ],
    },
    'installable': True,
    # 'application': True,
}