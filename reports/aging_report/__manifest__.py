# -*- coding: utf-8 -*-
{
    'name': "Aging Report",

    'summary': """
       Report""",

    #'description': """
     #   Long description of module's purpose
    #""",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','prioritization_engine'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'reports/todo_task_report.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
