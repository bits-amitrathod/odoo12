# -*- coding: utf-8 -*-
{
    'name': " Vendor Offer",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase','sale','product_brand','prioritization_engine','product_expiry_extension','delivery'],

    # always loaded
    # 'qweb': [
    #         'static/src/xml/tree_view_button.xml'
    #     ],
    'data': [
        'security/res_vendor_offer.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'demo/data.xml',
        'report/vendor_offer_reports.xml',
        'data/mail_template_data.xml',
        'report/vendor_offer_quotation_templates.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
        'views/tier_multiplier.xml',
        'views/vendor_pricing.xml',
        'views/views_app.xml',
        'views/threshold.xml'
        'report/vendor_offer_quotation_templates_acceleration.xml'
        # 'views/tree_view_asset.xml'

    ],

    'application' :True,
    'auto-install': False,
    'installable': True,
}
