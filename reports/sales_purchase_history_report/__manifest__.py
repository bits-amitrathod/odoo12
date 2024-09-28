
{
    'name': 'Sales purchase History',
    'summary':"Report",
    'category': 'sale',
    'version': '11.0.0.1',
    # 'summary': 'This module provides Sales purchase History',
    'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    # 'description': '''This module provides  sale purchase History.
    #                   With the help of this moudule you can print sales purchase History .
    #                   '''
    #                ,
    'depends': ['base', 'sale_management','contract_searching'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'report/saleperson_report.xml',
        'report/saleperson_temp.xml'
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
