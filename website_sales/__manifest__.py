# -*- coding: utf-8 -*-
{
    'name': "eCommerce CSTM",

    'summary': """
        Provide feature for product expiration lot
        
        """,

    'description': """
        Provide feature for product expiration lot
    """,

    'sequence': 57,

    # 'author': "",
    # 'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        # 'data/website_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
