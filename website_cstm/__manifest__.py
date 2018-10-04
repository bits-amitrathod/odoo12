# -*- coding: utf-8 -*-
{
    'name': "website CSTM",

     'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 57,
    'category': 'website',
    'version': '0.1',

    'depends': ['website_sales','website_product_brand','web_search','website_crm','prioritization_engine','mass_mailing'],

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
        'views/porduct_catalog.xml',
        'views/in_stock_notification.xml'
    ],

    # 'auto_install': True,
    'application': True,
    'installable': True,
}