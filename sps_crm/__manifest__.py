# -*- coding: utf-8 -*-
{
    'name': 'SPS CRM',
    'version': '1.2',
    'category': 'Purchase/CRM',
    'sequence': 15,
    'summary': '',
    'description': "",
    'website': '',
    'depends': [
        'base',
        'crm',
        'purchase',
        'vendor_offer',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/sps_crm_purchase_lead_views.xml',
        'views/sps_crm_purchase_lost_reason_views.xml',
        'views/sps_crm_purchase_tag_views.xml',
        'views/sps_crm_stage_views.xml',
        'views/sps_crm_menu_views.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
