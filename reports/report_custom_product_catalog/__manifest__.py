{
    'name': 'Report Product Catalog',
    'category': 'sale',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'stock','product','prioritization_engine'],
    'data': [
        'views/catalog_view.xml',
        'report/product_catalog_report.xml',
        'report/product_catalog_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}