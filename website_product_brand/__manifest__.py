# -*- coding: utf-8 -*-
{
    'name': "Product Brand in Website",

    'author': 'Benchmark It Solutions',
    'sequence': 60,
    'category': 'e-commerce',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['product_brand','website_sale'],

    'data': [
        # 'security/ir.model.access.csv',
        "security/ir.model.access.csv",
        "views/product_brand.xml",
    ],

    # 'application': True,
    'auto-install': True,
    'installable': True,
}