# -*- coding: utf-8 -*-
from odoo import models, fields

class WebResource(models.Model):
    _name = 'resource.webresource'

    title = fields.Char(string='Resource Title', required=True)
    description = fields.Char(string='Resource Description', required=True)
    url = fields.Char(string='Resource URL', required=True)
    is_active = fields.Boolean(string='Active', required=True)