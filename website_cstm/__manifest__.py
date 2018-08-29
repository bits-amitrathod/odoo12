# -*- coding: utf-8 -*-
{
    'name': "website CSTM",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'sequence': 57,

    # 'author': "My Company",
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website_sales','website_product_brand'],

    # always loaded
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
        'views/login.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    # 'auto_install': True,
    'application': True,
    'installable': True,
}