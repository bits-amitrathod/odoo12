
{
    'name': 'Report Compare Sale By Month',
    'category': 'Report',
    'version': '11.0.0.1',
    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base','product','sale'],
    'data': [
        'views/comp_sale_by_month_view.xml',
        'report/comp_sale_by_month_report.xml',
        'report/comp_sale_by_month_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
    
}
