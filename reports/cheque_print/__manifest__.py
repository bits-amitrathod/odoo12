# -*- coding: utf-8 -*-
{
    'name': "cheque print",

    'summary': """
          Report
    """,

    # 'description': """
    #
    # """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'category': 'Uncategorized',
    'version': '0.1',


    'depends': ['base'],

    # always loaded
    'data': [
        'report/cheque_print_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
