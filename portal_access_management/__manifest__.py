# -*- coding: utf-8 -*-
{
    'name': "Portal Access Management",
    'author': "Benchmark IT Solutions",
    'category': 'Portal Access',
    'version': '11.0.0.1',

    # any module necessary for this one to work correctly
     'depends': ['base', 'portal'],

    # always loaded
    'data': [
         'views/portal_access_scheduler.xml',
         'data/portal_data.xml',
         'views/views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}