# -*- coding: utf-8 -*-
{
    'name': "eCommerce CSTM",

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'sequence': 59,
    'category': 'e-commerce',
    'version': '1.0',
    'depends': ['website_sale','payment_aquirer_cstm'],
    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    # 'application': True,
}
