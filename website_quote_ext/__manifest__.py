# -*- coding: utf-8 -*-
{
    'name': "Online Proposals for Prioritization",


    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','prioritization_engine','vendor_offer','sps_theme','portal'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
    ],
    
}
