# -*- coding: utf-8 -*-
{

    'name': "Customer Credit Note",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkit.solutions",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','prioritization_engine'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets':{
        'web.assets_backend':[
            'customer_credit_note/static/src/js/thread.js',
        ],
    },
    # only loaded in demonstration mode

    'application': True,
    'auto-install': True,
    'installable': True,
    'license': 'LGPL-3',

}
