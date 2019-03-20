# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):

    _name = 'popup.product.on.order'
    _description = 'Products On Order'

    compute_at_date = fields.Selection([
        (0, 'This Month '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.Datetime.now)

    end_date = fields.Date('End Date', default = fields.Datetime.now)

    product_id = fields.Many2one('product.product', string='Product', required=False)

    customer_id = fields.Many2one('res.partner', string='Customer', required=False,)

    def open_table(self):
        tree_view_id = self.env.ref('products_on_order.products_on_orderlist_view').id
        form_view_id = self.env.ref('products_on_order.products_on_orderform_view').id

        if self.compute_at_date:
            s_date = ProductSaleByCountPopUp.string_to_date(str(self.start_date))
            e_date = ProductSaleByCountPopUp.string_to_date(str(self.end_date))
        else:
            e_date = datetime.date.today()
            s_date = datetime.date.today().replace(day=1)

        products_on_order_context = {}

        if self.customer_id.id:
            products_on_order_context.update({'partner_id': self.customer_id.id})

        if self.product_id.id:
            products_on_order_context.update({'product_id': self.product_id.id})

        self.env['report.products.on.order'].with_context(products_on_order_context).delete_and_create()

        domain = [('date_ordered', '>=', s_date), ('date_ordered', '<=', e_date)]

        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Products On Order'),
            'res_model': 'report.products.on.order',
            'context': {'group_by': 'product_id',},
            'domain' : domain,
            'target': 'main',
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()