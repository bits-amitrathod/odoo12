# -*- coding: utf-8 -*-
from typing import Dict, Any
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)



class PporoductTemplate(models.Model):
    _inherit = "product.template"


    def _default_public_categ_ids(self):
        return self.env['product.public.category'].search([('name', 'like', 'All')], limit=1)

    public_categ_ids = fields.Many2many('product.public.category', string='Website Product Category',
                                        help="The product will be available in each mentioned e-commerce category. Go to"
                                             "Shop > Customize and enable 'E-commerce categories' to view all e-commerce categories.",
                                        default=_default_public_categ_ids)