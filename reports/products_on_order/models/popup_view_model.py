# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__
                            )

class ProductSaleByCountPopUp(models.TransientModel):
    _name = 'prod_on_order.popup'
    _description = 'Products On Order'

    compute_at_date = fields.Selection([
        (0, 'This Month '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Datetime('Start Date', default=fields.Datetime.now)

    end_date = fields.Datetime('End Date', default = fields.Datetime.now)

    product_id = fields.Many2one('product.product', string='Product', required=False)

    customer_id = fields.Many2one('res.partner', string='Customer', required=False,)



    def open_table(self):
        tree_view_id = self.env.ref('products_on_order.list_view').id
        form_view_id = self.env.ref('sale.view_order_form').id

        if self.compute_at_date:
            s_date = ProductSaleByCountPopUp.string_to_date(str(self.start_date))
            e_date = ProductSaleByCountPopUp.string_to_date(str(self.end_date))
        else:
            cur_date_time = str(datetime.datetime.now())
            try:
                cur_date_time.index('.')
                cur_date_time = cur_date_time.split('.')[0]
            except:
                error = 1

            e_date = ProductSaleByCountPopUp.string_to_date(cur_date_time)

            first_date_time = str(datetime.datetime.now().replace(day=1))
            try:
                first_date_time.index('.')
                first_date_time = first_date_time.split('.')[0]
            except:
                error = 1

            s_date = ProductSaleByCountPopUp.string_to_date(first_date_time)



        # domain = []

        context = {}

        if self.product_id:
            # domain.append(['product_id', '=', self.product_id.id])
            context.update({'product_id' : self.product_id.id})

        if self.customer_id:
            # domain.append(['customer_id', '=', self.customer_id.id])
            context.update({'customer_id': self.customer_id.id})

        self.env['products.on_order'].with_context(context).delete_and_create()

        # sale_orders = self.env['products.on_order'].search(domain)
        #
        # order_ids = []
        # ids = []
        # for sale_order in sale_orders:
        #     if s_date <= ProductSaleByCountPopUp.string_to_date(sale_order.date_ordered) <= e_date:
        #         try:
        #             order_ids.index(sale_order.order_id)
        #         except:
        #             ids.append(sale_order.id)
        #             order_ids.append(sale_order.order_id)

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree, form',
            'name': _('Products On Order'),
            'res_model': 'products.on_order',
            # 'domain': [('id', 'in', ids)],
            'target': 'main'
        }

        _logger.info('action %r', action)

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATETIME_FORMAT).date()

