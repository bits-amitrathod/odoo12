{
        'name': 'Account Pass',
        'description': '',
        'author': 'benchmarkitsolutions',
        'depends': ['base', 'customize_sales_order'],
        'application': True,
        'version': '14.0.1.0.0',
        'license': 'AGPL-3',
        'support': '',
        'website': '',
        'installable': True,

        'data': [
            'security/ir.model.access.csv',
            'datas/data.xml',
            'views/templates.xml',
            'views/account_pass_views.xml',
            'views/account_pass_stage_views.xml',
            'views/customer_view.xml',
            ],
}

