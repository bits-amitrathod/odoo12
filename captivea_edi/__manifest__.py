# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Captivea EDI',
    'version': '7.0',
    'author': 'Captivea LLC',
    'summary': 'Handle EDI documents',
    'category': 'Extra Tools',
    'website': 'https://www.captivea.us',
    'depends': ['sale_stock', 'delivery'],
    'data': [
        'security/captivea_edi_security_groups.xml',
        'security/ir.model.access.csv',
        'data/edi_log_seq.xml',
        'views/account_move_views.xml',
        'views/sftp.xml',
        'views/captivea_edi_views.xml',
        'views/captivea_edi_wizard_views.xml',
        'views/captivea_menu.xml',
        'views/sale_views.xml',
        'views/stock_picking_views.xml',
        'data/ir_cron_jobs.xml',
        # 'views/res_partner_views.xml',
        'views/setu_edi_export_views.xml',
        'views/log_remove.xml',
        'views/product_template.xml',
        'views/customer_uom_conf.xml',
        'data/cron_log_remove.xml'

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
