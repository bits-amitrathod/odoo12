# -*- coding: utf-8 -*-
{
    'name': "Product Expiry Extension",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product_expiry','inventory_extension'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/scrap_scheduler_views.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/production_lot.xml',
        'views/stock_move_line_extension.xml',
        'views/stock_quant_ext.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}