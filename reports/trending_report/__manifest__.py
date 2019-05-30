

{
    'name': 'Trending Report',
    'summary':"Report",
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'sale_management'],
    'data': [
        'views/trending_report_list.xml',
        'report/trending_report_list_report.xml',
        'report/trending_report_list_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
