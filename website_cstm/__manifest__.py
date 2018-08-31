# -*- coding: utf-8 -*-
{
    'name': "website CSTM",

    'summary': """
       Website Theme and Features""",

    'description': """
         Website Theme and Features
    """,

    'sequence': 57,
    'category': 'website',
    'version': '0.1',

    'depends': ['website_sales','stock','website_product_brand','web_search'],

    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'views/views.xml',
        'views/templates.xml',

        'views/home.xml',
        'views/contact.xml',
        'views/faqs.xml',
        'views/about.xml',
        'views/ecommerce.xml',
        'views/quality_assurance.xml',
        'views/product-types.xml',
        'views/login.xml',
        'views/search.xml',
        'views/quickView.xml'
    ],

    # 'auto_install': True,
    'application': True,
    'installable': True,
}