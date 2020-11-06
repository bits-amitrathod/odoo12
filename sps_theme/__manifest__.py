# -*- coding: utf-8 -*-
{
    'name': "sps theme",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 57,
    'version': '0.1',
    'category': 'Theme/Creative',
    'depends': ['website_sales','website_product_brand','web_search','auth_signup','prioritization_engine','vendor_offer','website_crm','mass_mailing','website_slides'],

    'data': [
        'security/ir.model.access.csv',
        'views/website_template.xml',
        'data/theme_data.xml',


        'views/about_page.xml',
        'views/contact_page.xml',
        'views/stockhawk_page.xml',
        'views/career_page.xml',
        'views/faqs_page.xml',
        'views/equipment_repair_and_service_page.xml',
        'views/home_page.xml',
        'views/equipment_sell_page.xml',
        'views/request_a_quote_page.xml',
        'views/thank_you_page.xml',
        'views/surgical_products_sell_page.xml',
        'views/cart_lines_page.xml',
        'views/modal_optional_products_view.xml',
        'views/mile_templates.xml',
        'views/product_expiration_lot_view.xml',


        # 'views/menu.xml'

    ],

    'images': [

    ],

    # 'auto_install': True,
    # 'application': True,
    'installable': True,
}
