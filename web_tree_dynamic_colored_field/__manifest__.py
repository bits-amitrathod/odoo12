# Copyright 2015-2018 Camptocamp SA, Damien Crier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Colorize field in tree views',
    'summary': 'Allows you to dynamically color fields on tree views',
    'category': 'Hidden/Dependency',
    'version': '11.0.1.0.1',
    'depends': ['web'],
    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    'demo': [
        "demo/res_users.xml",
    ],
    'data': [
        'views/web_tree_dynamic_colored_field.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
