# -*- coding: utf-8 -*-
{
    'name': "Pick Ticket",

    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'category': 'sale',
    'version': '11.0.0.1',

    # any module necessary for this one to work correctly
     'depends': ['base', 'product','stock','prioritization_engine'],

    # always loaded
    'data': [
        'security/res_pick_ticket.xml',
        'security/ir.model.access.csv',
        'views/pick_ticket.xml',
        'reports/pick_ticket.xml',
        'reports/pick_ticket_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}