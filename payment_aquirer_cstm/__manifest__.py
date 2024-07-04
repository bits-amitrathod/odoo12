# -*- coding: utf-8 -*-
{
    'name': " Purchase order Payment Provider",
    'description': """
        Purchase order Payment Provider 
    """,

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'sequence': 59,
    'category': 'e-commerce',
    'version': '0.1',

    'depends': ['base','payment','website_sale','website_sale_delivery'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'data/payment_provider_cstm_data.xml',

    ],

    'installable': True,
    # 'application': True,
    "license" : "LGPL-3",
}
