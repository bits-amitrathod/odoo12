{
    'name': "Inventory Valuation Summary",

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
        # 'views/views.xml',
        # 'report/report_inventory_valuation_summary.xml',
        # 'report/inventory_valuation_summary.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}