# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):
    _name = 'salesbymonth.popup'
    _description = 'Sales By Count'


    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Datetime('Start Date', default=fields.Datetime.now)

    end_date = fields.Datetime('End Date', default = fields.Datetime.now)

    product_sku_code = fields.Char('Product SKU')

    def open_table(self):
        tree_view_id = self.env.ref('sales_by_month.list_view').id
        form_view_id = self.env.ref('product.product_normal_form_view').id

        if self.compute_at_date:
            s_date = ProductSaleByCountPopUp.string_to_date(str(self.start_date))
            e_date = ProductSaleByCountPopUp.string_to_date(str(self.end_date))

            sale_orders = self.env['sale.order'].search([])

            filtered_sale_orders = list(filter(
                lambda x: x.confirmation_date and \
                          s_date <= ProductSaleByCountPopUp.string_to_date(x.confirmation_date) <= e_date, sale_orders))
            product_ids = []
            for sale_order in filtered_sale_orders:
                for sale_order_line in sale_order.order_line:
                    product_ids.append(sale_order_line.product_id.id)

            product_ids = list(set(product_ids))

            _logger.info('ids : %r', product_ids)

            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Sales By Month'),
                'res_model': 'product.product',
                'domain': [('id', 'in', product_ids)],
                'target': 'main'
            }
            if self.product_sku_code:
                action['domain'].append(('product_tmpl_id.sku_code', 'ilike', self.product_sku_code))
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Sales By Month'),
                'res_model': 'product.product',
                'domain': [],
                'target': 'main'
            }
            if self.product_sku_code:
                action['domain'].append(('product_tmpl_id.sku_code', 'ilike', self.product_sku_code))
        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATETIME_FORMAT).date()

