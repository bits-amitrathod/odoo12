# -*- coding: utf-8 -*-
{
    'name': "Short date and over stocked product sold by KA",

    'summary': """
      Report
       """,

    'description': """

    """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '1.0',

    'depends': ['product_expiry_extension'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/product_sold_by_ka_report.xml',
        'report/product_sold_by_ka_report_template.xml'
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}