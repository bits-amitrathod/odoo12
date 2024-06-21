# -*- coding: utf-8 -*-
{
    'name': "Lot History",

    'summary': """
     Report
        """,

    'description': """
        
    """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",


    'category': 'Report',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','prioritization_engine'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'reports/todo_task_report.xml',
        # 'views/templates.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
