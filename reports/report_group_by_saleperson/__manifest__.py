{
    'name': 'Gross Sales By Salesperson',
    'category': 'sale',
    'version': '11.0.0.1',
    'author': 'Benchmark It Solutions',
    'depends': ['base', 'sale', 'sale_order_dates'],
    'data': [
        'views/groupby_view.xml',
        'report/group_by_sales_person_report.xml',
        'report/group_by_sales_person_temp.xml',
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': False,
}
