{
    'name': "Inventory Valuation Summary",

    'summary': """
      Inventory Valuation Summary
      """,

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",

    'category': 'Report',
    'version': '0.1',

    'depends': ['stock_account','prioritization_engine'],

    'data': [
        'views/views.xml',
        'report/report_inventory_valuation_summary.xml',
        'report/inventory_valuation_summary.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
