# Copyright 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2013 Camptocamp SA (author: Guewen Baconnier)
# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Website Automatic Workflow',
    'version': '11.0.1.0.0',
    'category': 'Sales Management',

    'license': 'AGPL-3',
       'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'depends': ['sale_stock',
                'sales_team',
                ],
    'data': [
            'security/ir.model.access.csv',
            'views/sale_view.xml',
            'views/sale_workflow_process_view.xml',
            'data/automatic_workflow_data.xml',

             ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
