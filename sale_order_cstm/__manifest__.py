# -*- coding: utf-8 -*-
{
    'name': "Sales Order Line Alert Message",


    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_stock','vendor_offer'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    'installable': True,

}