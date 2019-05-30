{
    'name': 'Gross Sales By Product',
    'summary':"Report",
    'category': 'sale',
    'version': '11.0.0.1',
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    'depends': ['base', 'sale_management'],
    'data': [
        'views/groupby_product_view.xml',
        'report/report_sales_groupby_product.xml',
        'report/sales_groupby_product.xml'
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
}
