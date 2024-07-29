from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class CustomerContract(models.Model):
    _name = "exclude.product.in.stock"
    _description = 'Exclude Product in Stock model'

    _inherits = {'product.product': 'product_id'}

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete="cascade")
    # exclude_in_stock = fields.Boolean("Exclude Product From In-Stock Notification?")

    _sql_constraints = [
        ('exclude_product_in_stock_uniq', 'unique (product_id,partner_id)',
         'In Exclude Product IN-Stock - Product is Repeated !')
    ]