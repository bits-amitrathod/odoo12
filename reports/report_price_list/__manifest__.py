
{
    'name': 'Customer and Product Price List Report',
    'summary':"Report",
    'category': 'sale',
    'version': '11.0.0.1',
    # 'summary': 'This module provides Product Price List Report.',
    # 'website': ' ',
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",
    # 'description': '''This module provides Product Price List Report.
    #                   With the help of this moudule you can print Product Price List .
    #                  '''
    #                ,
    'depends': ['base', 'product','stock','prioritization_engine'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/price_list_view.xml',
        # 'report/price_list_report.xml',
        # 'report/price_list_temp.xml'
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
}
