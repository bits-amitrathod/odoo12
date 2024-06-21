# -*- coding: utf-8 -*-
{
    'name': "MTD Sales",
    'summary': "Report",

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/mtd_report.xml',
        'report/mtd_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
