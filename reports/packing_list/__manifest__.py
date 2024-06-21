# -*- coding: utf-8 -*-
{
    'name': " Packing List",
     'summary':"Report",
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','sale','purchase','delivery','prioritization_engine'],
    # always loaded



    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'report/sale_packing_list_template.xml',
        # 'report/packing_list_report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
