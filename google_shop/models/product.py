# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

class ProductUpdates(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super(ProductUpdates, self).write(vals)
        fields_dict=self.env['field.mappning.line'].sudo().search([('fixed','=',False)])
        fields_name=[x['model_field_id']['name'] for x in fields_dict]
        fields_name.append('name')
        common_list=list(set.intersection(set(fields_name),set(vals)))
        if len(common_list)>0:
            for s in self:
                self.env['product.mapping'].sudo().search([('product_id','=',s.id)]).write({'product_status':'updated','update_status':False})
        return res
