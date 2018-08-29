# -*- coding: utf-8 -*-
{
    'name': "Product Brand Filtering in Website",

    'summary': """
        Prioritization Engine""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Amit Rathod",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'e-commerce',
    'version': '1.0',

    # any module necessary for this one to work correctly

    'depends': ['product_brand',
                'website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        "security/ir.model.access.csv",
        "views/product_brand.xml",
    ],

    # only loaded in demonstration mode
    'demo': [],
    # 'application': True,
    'auto-install': True,
    'installable': True,
}