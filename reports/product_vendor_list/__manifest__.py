

{
    'name': 'Product Vendor List',
    'summary':"Report",
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'purchase','prioritization_engine'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_vendor_list.xml',
        'report/product_vendor_list_report.xml',
        'report/product_vendor_list_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
