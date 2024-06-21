# -*- coding: utf-8 -*-
{
    'name': "Product Expiry Extension",

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','inventory_extension'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/scrap_scheduler_views.xml',
        'views/production_lot.xml',
        'views/stock_move_line_extension.xml',
        'views/stock_quant_ext.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'product_expiry_extension/static/src/less/customize.style.less',

        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}


