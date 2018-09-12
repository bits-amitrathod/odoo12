# -*- coding: utf-8 -*-
{
    'name': "website CSTM",

    'summary': """
       Website Theme and Features""",

    'description': """
         Website Theme and Features
    """,
    'author': 'Benchmark It Solutions',
    'sequence': 57,
    'category': 'website',
    'version': '0.1',

    'depends': ['website_sales','stock','website_product_brand','web_search','website_crm'],
# 'mass_mailing',

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
        'views/quickView.xml',
        'views/in_stock_notification.xml'
    ],

    # 'auto_install': True,
    'application': True,
    'installable': True,
}