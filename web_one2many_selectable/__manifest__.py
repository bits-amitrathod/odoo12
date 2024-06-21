# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2016 Shawn
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Multi-selection for one2many fields",
    "version": "1.0",
    'author': "Benchmark IT Solutions (I) Pvt Ltd.",
    'website': "http://www.benchmarkitsolutions.com",
    "summary": "This widget adds the capability for selecting multiple records in one2many fields and calls a python function with the recods as self argument",
    "description": '''
Description
-----------
This widget adds the capability for selecting multiple records in one2many fields and calls a python function with the ids as argument.

Its really easy to use, just add widget=one2many_selectable on any one2many field.

e.g. <field name="course_id" widget="one2many_selectable">
        <tree>
            <field name="title" />
        </tree>
    </field>

You can get the selected records in python function, a smple python function is as follows:

#@api.multi
def bulk_verify(self):
    for record in self:
	print record

By default the widget will pick model from one2many field and default function name is "bulk_verify".
You can change the model as well as python function name from javascript.
    ''',
    "category": "Web Enhancements",
    "depends": [
        'web',
    ],
    "data": [
    ],
    'assets': {
        'web.assets_backend': [
            'web_one2many_selectable/static/src/js/widgets.js',
            'web_one2many_selectable/static/src/xml/widget_view.xml',

        ],
    },
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': [],
    },
}
