# -*- coding: utf-8 -*-
{
    'name': 'Blog Cstm',
    'version': '1.0',
    'website': '',
    'category': 'bits',
    'summary': 'Blog Post customization',
    'author': 'BenchmarkItSolutions',
    'description': " Blog Post customization",
    'depends': ['base_setup', 'mail','website_blog'],
    'data': [
        'security/ir.model.access.csv',
        'views/blog_post_form.xml',
        'views/popular_post_template.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
