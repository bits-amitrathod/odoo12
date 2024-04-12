# -*- coding: utf-8 -*-
{
    'name': "Purchase History",

    'summary': "Report",

    'author': "Benchmark It Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','vendor_offer'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'reports/todo_task_report.xml',
        # 'views/views.xml'
    ],
   'installable': True,
   'auto_install': False,
   'application': True
}
