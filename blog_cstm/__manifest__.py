# -*- coding: utf-8 -*-
{
    'name': 'Blog Cstm',
    'version': '1.0',
    'website': '',
    'category': 'Others',
    'summary': 'Blog Post customization',
    'author': 'Benchmark',
    'description': " Blog Post customization",
    'depends': ['base_setup', 'mail','website_blog'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
