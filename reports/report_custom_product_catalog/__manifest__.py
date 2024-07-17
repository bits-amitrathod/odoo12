{
    'name': 'Product Catalog',
    'summary':"Report",
    'category': 'sale',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'stock','product','prioritization_engine'],
    'data': [
        'views/catalog_view.xml',
        'report/product_catalog_report.xml',
        'report/product_catalog_temp.xml',
        'security/ir.model.access.csv'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}