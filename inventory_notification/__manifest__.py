# -*- coding: utf-8 -*-
{
    'name': "Inventory Notification",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_setup','product', 'stock','vendor_offer','prioritization_engine','inventory_monitor','customize_sales_order','mail_bot'],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
         'views/inventory_notification_cron.xml',
         'views/inventory_notification_print_report.xml',
         'views/inventory_packing_list_notification.xml',
         'data/notification_mail_template.xml',
         'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': ['demo/demo.xml', ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',

}
