# -*- coding: utf-8 -*-
{
    'name': "eCommerce CSTM",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'sequence': 59,
    'category': 'e-commerce',
    'version': '1.0',
    'depends': ['base', 'product', 'sale','purchase', 'website_sale','payment_aquirer_cstm','vendor_offer'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/quote_my_report.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    # 'application': True,
}