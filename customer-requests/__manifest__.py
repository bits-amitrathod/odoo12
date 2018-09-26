# -*- coding: utf-8 -*-
{
    'name': "Customer Requests",

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fetchmail', 'sale', 'prioritization_engine'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/voided_product_template_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],

    'qweb': [
         'static/src/xml/template_import.xml'
    ],

    'js': [
         'static/src/js/base_import.js'
    ],

    'application' : True,
    'installable' : True,
    'auto_install' : True
}