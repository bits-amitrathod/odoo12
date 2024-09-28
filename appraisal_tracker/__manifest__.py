# -*- coding: utf-8 -*-
{

    'name': "Appraisal Tracker",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",



    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','vendor_offer','web_tree_dynamic_colored_field'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/apprisal_tracker_report_temp.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'auto-install': True,
    'installable': True,
}
