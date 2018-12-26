# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):
    _name = 'salesbymonth.popup'
    _description = 'Sales By Month'


    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    product_sku_code = fields.Char('Product SKU')

    def open_table(self):
        tree_view_id = self.env.ref('sales_by_month.list_view').id
        form_view_id = self.env.ref('product.product_normal_form_view').id
        if self.start_date and self.end_date :
            self.end_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d") + datetime.timedelta(days=1)
            margins_context = {'start_date': self.start_date, 'end_date': self.end_date}
        else:
            self.start_date = datetime.date.today().replace(day=1)
            self.end_date = datetime.date.today() + datetime.timedelta(days=1)
            margins_context = {'start_date': self.start_date, 'end_date': self.end_date}
        x_res_model = 'sales_by_month'
        self.env[x_res_model].with_context(margins_context).delete_and_create()

        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Sales By Month'),
                'res_model': x_res_model,
                'context':margins_context,
                'domain': [('total_sale_quantity', '>', 0)],
                'target': 'main'
            }
            if self.product_sku_code:
                action['domain'].append(('sku_code', 'ilike', self.product_sku_code))
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Sales By Month'),
                'res_model': x_res_model,
                'domain': [('total_sale_quantity', '>', 0)],
                'target': 'main'
            }
            if self.product_sku_code:
                action['domain'].append(('sku_code', 'ilike', self.product_sku_code))
        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATETIME_FORMAT).date()

