# -*- coding: utf-8 -*-
{
    'name': "sps theme",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'sequence': 57,
    'version': '0.1',
    'category': 'Theme/Creative',
    'depends': ['website', 'website_theme_install'],

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

        # 'views/menu.xml'

    ],

    'images': [

    ],

    # 'auto_install': True,
    # 'application': True,
    'installable': True,
}
