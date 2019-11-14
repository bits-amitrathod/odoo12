# -*- coding: utf-8 -*-
{
    'name': "Website CSTM",

     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 57,
    'category': 'Theme',
    'version': '0.1',
    'depends': ['website_sales','website_product_brand','web_search','auth_signup','prioritization_engine','vendor_offer','website_crm','mass_mailing'],

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
        'views/terms.xml',
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
        'views/career.xml'
        'views/mission.xml',
        'views/testimonials.xml'

    ],

    'images': [
        'static/description/sps_screenshot.jpg',
    ],

    # 'auto_install': True,
    # 'application': True,
    'installable': True,
}
