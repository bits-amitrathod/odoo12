# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'popup.view.model'

    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")
    product_id = fields.Many2many('product.product', string="Products")

    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")


    def open_table(self):

        tree_view_id = self.env.ref('purchase_history_custome.form_list').id
        form_view_id = self.env.ref('purchase.purchase_order_form').id
        if self.compute_at_date:

            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Purchase History'),
                'res_model': 'purchase.order',
                'context': {'product_id':self.product_id,'start_date':self.start_date,'end_date':self.end_date},
                'domain': [('date_order', '>=', self.start_date),('date_order', '<=', self.end_date)],
            }
            action.update({'target': 'main'})
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Purchase History'),
                'res_model': 'purchase.order',
            }
            action.update({'target': 'main'})
            return action

