# -*- coding: utf-8 -*-
{
    'name': "Broker Report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','apprisal_tracker'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/broker_report_view.xml',
        'views/templates.xml',
        'report/broker_report.xml',
        'report/broker_report_temp.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}