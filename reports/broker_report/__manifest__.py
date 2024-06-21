{
    'name': "Broker Report",
    'summary':"Report",
     'author': "Benchmark IT Solutions",
    'website': "http://www.benchmarkitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','appraisal_tracker'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/broker_report_view.xml',
        # 'views/templates.xml',
        # 'report/broker_report.xml',
        # 'report/broker_report_temp.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
