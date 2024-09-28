# -*- coding: utf-8 -*-
{
    'name': "Revenue By National Account Per Account Report",

    'summary': """Report""",

    # 'description': """
    #     Long description of module's purpose
    # """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkit.solutions",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale', 'appraisal_tracker'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/revenue_by_na_per_account_report.xml',
        'report/revenue_by_na_per_account_temp.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
