# -*- coding: utf-8 -*-
{
    'name': "SPS Receiving List",

    'summary': """
      Report
       """,

    'description': """

    """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '1.0',

    'depends': ['base', 'stock', 'stock_barcode', 'delivery'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'reports/sps_receiving_list.xml'
    ],
    'qweb': [
        'views/qweb_templates.xml',

    ],
    'assets': {
        'web.assets_backend':[
            'sps_receiving_list_report/static/js/settings_widget.js',
            'sps_receiving_list_report/static/js/picking_client_action.js',
        ]
    },

    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}