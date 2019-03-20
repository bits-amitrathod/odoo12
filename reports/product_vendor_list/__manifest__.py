

{
    'name': 'Product Vendor List',
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'purchase'],
    'data': [
        'views/product_vendor_list.xml',
        'report/product_vendor_list_report.xml',
        'report/product_vendor_list_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
