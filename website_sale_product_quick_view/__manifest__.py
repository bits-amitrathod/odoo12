# -*- coding: utf-8 -*-
{
    'name': "E-commerce Product Quick View",

    'summary': """
       E-commerce Product Quick View""",

    'description': """
        E-commerce Product Quick View
    """,

    'author': "Amit Rathod",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'eCommerce',
    'version': '1.0',

    # any module necessary for this one to work correctly

    'depends': ['base',
                'website_cstm',
                'website_mail',
                'rating'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/template.xml',
    ],

    # only loaded in demonstration mode
    'demo': [],
    # 'application': True,
    'auto-install': True,
    'installable': True,
}