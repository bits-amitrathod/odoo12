# -*- coding: utf-8 -*-
{
    'name': "Vendor Offer",

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase','sale','product_brand','prioritization_engine','product_expiry_extension'],

    # always loaded
    'data': [
        'security/res_vendor_offer.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'demo/data.xml',
        'report/vendor_offer_reports.xml',
        'data/mail_template_data.xml',
        'report/vendor_offer_quotation_templates.xml',

    ],

    'application' :True,
    'auto-install': True,
    'installable': True,
}
