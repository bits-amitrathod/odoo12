# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


# class PopUp(models.TransientModel):
#     _name = 'popup.view.model2'
#
#     start_date = fields.Date('Start Date')
#     end_date = fields.Date(string="End Date")
#     product_id = fields.Many2many('product.product', string="Products")
#
#     compute_at_date = fields.Selection([
#         (0, 'Show All'),
#
#     ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
#
#
#     def open_table(self):
#         tree_view_id = self.env.ref('lot_history.form_list').id
#         form_view_id = self.env.ref('stock.view_production_lot_form').id
#         if self.compute_at_date:
#
#
# 
#             action = {
#                 'type': 'ir.actions.act_window',
#                 'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
#                 'view_mode': 'tree,form',
#                 'name': _('Products'),
#                 'res_model': 'stock.production.lot',
#                 'domain': [('create_date', '>=', self.start_date),('create_date', '<=', self.end_date)],
#             }
#             return action
#         else:
#             action = {
#                 'type': 'ir.actions.act_window',
#                 'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
#                 'view_mode': 'tree,form',
#                 'name': _('Products'),
#                 'res_model': 'stock.production.lot',
#             }
#             return action
#
