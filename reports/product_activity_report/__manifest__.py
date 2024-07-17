{
    'name': "Product Activity Report",

    'summary': """
      Report
      """,

    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '0.1',

    'depends': ['stock_account','prioritization_engine'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/report_product_activity_report.xml',
        'report/product_activity_report.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
