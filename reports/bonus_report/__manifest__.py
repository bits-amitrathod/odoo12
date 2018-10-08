

{
    'name': 'Bonus Report',
    'category': 'Report',
    'version': '11.0.0.1',
     'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base', 'appraisal_tracker','purchase'],
    'data': [
        'views/bonus_report_view.xml',
        'report/bonus_report.xml',
        'report/bonus_report_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
