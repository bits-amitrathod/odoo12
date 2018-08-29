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
    'name': 'Sales purchase History',
    'category': 'sale',
    'version': '11.0.0.1',
    # 'summary': 'This module provides Sales purchase History',
    'author': 'Tushar Godase',
    # 'description': '''This module provides  sale purchase History.
    #                   With the help of this moudule you can print sales purchase History .
    #                   '''
    #                ,
    'depends': ['base', 'sale_management'],
    'data': [
        'views/sale_view.xml',
        'report/saleperson_report.xml',
        'report/saleperson_temp.xml'
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': False,
}
