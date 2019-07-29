# -*- coding: utf-8 -*-
{
    'name': "Portal Access Management",
    'author': "Benchmark IT Solutions",
    'category': 'Portal Access',
    'version': '11.0.0.1',

    # any module necessary for this one to work correctly
     'depends': ['base'],

    # always loaded
    'data': [
         'views/views.xml',
         'views/templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}