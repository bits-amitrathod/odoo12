
{
    'name': ' Discount Summary ',
    'summary':"Report",
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/discount_summary_view.xml',
        'report/discount_summary_report.xml',
        'report/discount_summary_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
