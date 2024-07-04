# -*- coding: utf-8 -*-
{
    'name': "eCommerce CSTM",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 59,
    'category': 'e-commerce',
    'version': '1.0',
    'depends': ['website_sale','sale_product_configurator', 'payment_aquirer_cstm','vendor_offer'],
    'data': [
        'security/ir.model.access.csv',
        'data/data_views.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/quote_my_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sales/static/src/js/quote_my_report.js',
        ],
    },
    'installable': True,
    # 'application': True,
    "license": "LGPL-3",

}