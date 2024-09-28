# -*- coding: utf-8 -*-
{
	'name': 'Res Website',
	'version': '12.0.1.0.0',
	'summary': 'Information',
	'category': 'Tools',
	'author': 'benchmark it solutions',
	'maintainer': 'benchmark it solutions',
	'company': 'benchmark it solutions',
	'website': 'benchmark it solutions',
	'depends': ['base','website','website_sale','website_blog','website_slides'],
	'data': [
		'security/ir.model.access.csv',
		'views/resources_page.xml',
		'views/views.xml',
	],
	'images': [],
	'license': 'AGPL-3',
	'installable': True,
	'application': False,
	'auto_install': False,
}
