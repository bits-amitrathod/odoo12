# -*- coding: utf-8 -*-
{
    'name': " Purchase order Payment acquirer",
    'description': """
        Purchase order Payment acquirer 
    """,

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'sequence': 59,
    'category': 'e-commerce',
    'version': '0.1',

    'depends': ['base','payment','website_sale','website_sale_delivery'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
        # 'data/payment_acquirer_cstm_data.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],

    'installable': True,
    # 'application': True,
}
