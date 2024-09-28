# -*- coding: utf-8 -*-
{
    'name': "Customer Requests ",


    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'prioritization_engine'],

    # always loaded
    'data': [
        'security/res_user_cust_requests.xml',
        'security/ir.model.access.csv',
        'views/remove_document_scheduler.xml',
        'views/voided_product_template_views.xml',
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'customer-requests/static/src/js/template_import.js',
            'customer-requests/static/src/xml/template_import.xml',
        ],
    },
    'application' : True,
    'installable' : True,
    'auto_install' : True,
    'license': 'LGPL-3',

}