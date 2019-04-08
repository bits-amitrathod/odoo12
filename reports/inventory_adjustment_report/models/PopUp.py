# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'adj_popup.view.model'


    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")
    # product_id = fields.Many2many('product.product', string="Products")

    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")

    product_sku_code = fields.Char('Product SKU')

    def open_table(self):
        tree_view_id = self.env.ref('inventory_adjustment_report.form_list_adjustment').id
        form_view_id = self.env.ref('stock.view_move_line_form').id
        domain = ['&', ('location_id.name', 'in', ['Inventory adjustment','Input','Stock']), ('location_dest_id.name', 'in', ['Scrapped','Input','Stock'])]
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Inventory Adjustment'),
            'res_model': 'stock.move.line',
            'domain': domain,
        }

        if self.compute_at_date:
            action['domain'].append(('date', '>=', self.start_date))
            action['domain'].append(('date', '<=', self.end_date))
            if self.product_sku_code:
                action['domain'].append(('product_id.product_tmpl_id.sku_code', 'ilike', self.product_sku_code))
            action.update({'target': 'main'})
            return action
        else:
            if self.product_sku_code:
                action['domain'].append(('product_id.product_tmpl_id.sku_code', 'ilike', self.product_sku_code))
            action.update({'target': 'main'})
            return action




