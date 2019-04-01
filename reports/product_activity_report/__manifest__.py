{
    'name': "Product Activity Report",

    'summary': """
      Product Activity Report
      """,

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '0.1',

    'depends': ['stock_account','prioritization_engine','product_expiry_extension'],

    'data': [
        'views/views.xml',
        'report/report_product_activity_report.xml',
        'report/product_activity_report.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
