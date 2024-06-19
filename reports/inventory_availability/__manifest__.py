# -*- coding: utf-8 -*-
{
    'name': "Inventory Availability",
    'summary':"Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','stock','vendor_offer'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_availability.xml',
        'views/inventory_availability_print.xml',
        'views/inventory_availability_pdf.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
