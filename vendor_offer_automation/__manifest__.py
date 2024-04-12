# -*- coding: utf-8 -*-
{
    'name': "Vendor Offer Automation",

    'author': "Benchmark IT Solutions (I) Pvt. Ltd",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctlyd
    'depends': ['web', 'vendor_offer'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',

    ],
    'assets':{
        'web.assets_backend': [
            'vendor_offer_automation/static/src/js/offer_template_widget.js',
            'vendor_offer_automation/static/src/xml/offer_template_widget.xml',
        ],
    },

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'auto_install': True
}
