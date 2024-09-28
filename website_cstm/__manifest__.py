# -*- coding: utf-8 -*-
{
    'name': "Website CSTM",

     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 57,
    'category': 'Theme',
    'version': '0.1',
    'depends': ['website_sales','website_product_brand','web_search','auth_signup','prioritization_engine','vendor_offer','website_crm','mass_mailing','website_slides'],

    'data': [
        'views/templates.xml',
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'views/views.xml',
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
        'views/terms_of_sale.xml',
        'views/terms_of_purchase.xml',
        'views/in_stock_notification.xml',
        'views/stockhawk.xml',
        'views/sell.xml',
        'views/equipment.xml',
        'views/purchase_product.xml',
        'views/vendor_list.xml',
        'views/seller.xml',
        'views/equipment_service_request.xml',
        'views/request_quote.xml',
        'views/repair.xml',
        'views/repair_service_request.xml',
        'views/why_need_us.xml',
        'views/career.xml',
        'views/mission.xml',
        'views/testimonials.xml',
        'views/thank_you.xml'
    ],

    'images': [
        'static/description/sps_screenshot.jpg',
    ],

    # 'auto_install': True,
    # 'application': True,
    'installable': True,
    'license': 'AGPL-3'
}
