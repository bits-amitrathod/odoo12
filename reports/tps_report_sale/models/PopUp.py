# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'popup.view.model123'

    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")


    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")

    def open_table(self):
        tree_view_id = self.env.ref('tps_report_sale.form_list_tps').id
        form_view_id = self.env.ref('product.product_normal_form_view').id

        if self.compute_at_date:
            # s_date = PopUp.string_to_date(str(self.start_date))
            # e_date = PopUp.string_to_date(str(self.end_date))

            filtered_sale_orders = self.env['sale.order'].search([('confirmation_date', '>=', self.start_date),('confirmation_date','<=', self.end_date)])

            product_ids = []
            for sale_order in filtered_sale_orders:
                for sale_order_line in sale_order.order_line:
                    product_ids.append(sale_order_line.product_id.id)

            product_ids = list(set(product_ids))



            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Total Product Sales'),
                'res_model': 'product.product',
                'domain': [('id', 'in', product_ids)],
                'target': 'main'
            }
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Total Product Sales'),
                'res_model': 'product.product',
                'target': 'main'
            }
        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATETIME_FORMAT).date()
