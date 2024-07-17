# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.http_routing.models.ir_http import slug

class FieldMapping(models.Model):
    _name = 'field.mappning'
    _description = " Fields Mapping "

    name = fields.Char(string="Name",required=True)
    active = fields.Boolean(string="Active",default=True)
    field_mapping_line_ids = fields.One2many(comodel_name='field.mappning.line',inverse_name='field_mapping_id',string="Fileds To Mapped")
