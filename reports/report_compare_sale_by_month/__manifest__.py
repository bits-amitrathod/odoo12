
{
    'name': 'Compare Sales By Month',
    'summary':"Report",
    'category': 'Report',
    'version': '11.0.0.1',
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['base','product','sale','prioritization_engine'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/comp_sale_by_month_view.xml',
        # 'report/comp_sale_by_month_report.xml',
        # 'report/comp_sale_by_month_temp.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': True,

}
