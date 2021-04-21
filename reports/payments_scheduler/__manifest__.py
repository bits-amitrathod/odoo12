
{
    'name': ' Payments Scheduled',
    'summary':"Report",
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/payments_scheduler_view.xml',
        'report/payments_scheduler_report.xml',
        'report/payments_scheduler_report_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
