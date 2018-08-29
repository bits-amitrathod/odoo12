# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': 'Product Price List',
    'category': 'sale',
    'version': '11.0.0.1',
    # 'summary': 'This module provides Product Price List Report.',
    # 'website': ' ',
    'author': 'Akash Ingole',
    'license': 'AGPL-3',
    # 'description': '''This module provides Product Price List Report.
    #                   With the help of this moudule you can print Product Price List .
    #                  '''
    #                ,
    'depends': ['base', 'sale_management','stock'],
    'data': [
        'views/price_list_view.xml',
        'report/price_list_report.xml',
        'report/price_list_temp.xml'
    ],
    'images': ['static/description/banner.png'],
    'auto_install': True,
    'installable': True,
    'application': True,
}
