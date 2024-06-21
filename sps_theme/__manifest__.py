# -*- coding: utf-8 -*-
{
    'name': "sps theme",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 57,
    'version': '0.1',
    'category': 'Theme/Creative',
    'depends': ['website_sale', 'website_sales','website_product_brand','web_search','auth_signup','prioritization_engine','vendor_offer','website_crm','mass_mailing','website_slides','blog_cstm'],

    'data': [
        'security/ir.model.access.csv',
        'views/website_template.xml',
        'data/theme_data.xml',
        'data/ir_asset.xml',
        'views/about_page.xml',
        'views/career_page.xml',
        'views/our_team_page.xml',
        'views/contact_page.xml',
        'views/portal_my_details.xml',
        'views/stockhawk_page.xml',
        'views/seller_form_page.xml',
        'views/equipment_service_request_page.xml',
        'views/vendor_list_page.xml',
        'views/notify_me_template.xml',
        'views/faqs_page.xml',
        'views/cart_page.xml',
        'views/login_page.xml',
        'views/equipment_repair_and_service_page.xml',
        'views/quality_assurance_page.xml',
        'views/home_page.xml',
        'views/equipment_sell_page.xml',
        'views/request_a_quote_page.xml',
        'views/thank_you_page.xml',
        'views/surgical_products_sell_page.xml',
        'views/product_catagory_and_brand_template.xml',
        'views/website_product_page.xml',
        'views/cart_lines_page.xml',
        'views/website_header_template.xml',
        'views/website_footer_template.xml',
        'views/website_shop_templates.xml',
        'views/porduct_catalog_page.xml',
        'views/terms_and_conditions_page.xml',
        'views/policy_page.xml',
        'views/terms_of_sale_page.xml',
        'views/terms_of_purchase_page.xml',
        'views/menu.xml'
    ],

    # 'auto_install': True,
    'application': True,
    'installable': True,
}
