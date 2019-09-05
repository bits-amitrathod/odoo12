# -*- coding: utf-8 -*-
{
    'name': "Inventory Monitor",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','product_brand','vendor_offer','inventory_extension','purchase'],
    # always loaded

    'data': [
        'views/inventory_monitor.xml',
        'views/inventory_monitor_print.xml',
        'views/inventory_monitor_print_report.xml',
        'security/ir.model.access.csv',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
