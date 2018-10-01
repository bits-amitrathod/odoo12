# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


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
            if '.' in cur_date_time:
                cur_date_time = cur_date_time.split('.')[0]

            first_date_time = str(datetime.datetime.now().replace(day=1))
            if '.' in first_date_time:
                first_date_time = first_date_time.split('.')[0]

            e_date = ProductSaleByCountPopUp.string_to_date(cur_date_time)
            s_date = ProductSaleByCountPopUp.string_to_date(first_date_time)

        sale_order_domain = [('confirmation_date', '!=', False)]

        if self.customer_id.id:
            sale_order_domain.append(('partner_id', '=', self.customer_id.id))

        confirmed_sale_orders = self.env['sale.order'].search(sale_order_domain)

        product_id = self.product_id

        sale_order_ids, sale_order_prod_ids = ProductSaleByCountPopUp.update_orders(confirmed_sale_orders, s_date, e_date, product_id)

        if product_id:
            domain = [('id', 'in', sale_order_prod_ids)]
        else:
            domain = [('id', 'in', sale_order_ids)]

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), [form_view_id, 'form']],
            'view_mode': 'tree, form',
            'name': _('Products On Order'),
            'res_model': 'sale.order',
            'domain': domain,
            'target': 'main'
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATETIME_FORMAT).date()

    @staticmethod
    def update_orders(confirmed_sale_orders, s_date, e_date, product_id):
        sale_order_ids = []
        sale_order_prod_ids = []
        for sale_order in confirmed_sale_orders:
            if s_date <= ProductSaleByCountPopUp.string_to_date(str(sale_order.confirmation_date)) <= e_date:
                qty_ordered = qty_remaining = 0
                for sale_order_line in sale_order.order_line:
                    if product_id and sale_order_line.product_id.id == product_id.id:
                        sale_order.qty_ordered = sale_order_line.product_uom_qty
                        sale_order.qty_remaining = sale_order_line.product_uom_qty - sale_order_line.qty_delivered
                        qty_remaining = qty_remaining + sale_order.qty_remaining
                        qty_ordered = qty_ordered + sale_order.qty_ordered
                        sale_order_prod_ids.append(sale_order.id)
                        # break
                    else:
                        qty_ordered = qty_ordered + sale_order_line.product_uom_qty
                        qty_remaining = qty_remaining + (
                                sale_order_line.product_uom_qty - sale_order_line.qty_delivered)
                if not product_id:
                    sale_order.qty_ordered = qty_ordered
                    sale_order.qty_remaining = qty_remaining

                sale_order.qty_total_remaining = qty_remaining
                sale_order_ids.append(sale_order.id)

        return sale_order_ids, sale_order_prod_ids


class ProductSaleByCountSaleModel(models.Model):
    _inherit = 'sale.order'
    customer_name = fields.Char(string='Customer Name', compute='set_customer')
    qty_ordered = fields.Float(string="Qty Ordered", )
    qty_remaining = fields.Float(string="Qty Remaining",)
    qty_total_remaining = fields.Float(string="Total SO Items Remaining",)
    # calculate_data = fields.Boolean(default=False)


    @api.multi
    def set_customer(self):
        for sale_order in self:
            sale_order.customer_name = str(sale_order.partner_id.display_name)
            # qty_ordered = qty_remaining = 0
            # for sale_order_line in sale_order.order_line:
            #     qty_ordered = qty_ordered + sale_order_line.product_uom_qty
            #     qty_remaining = qty_remaining + (
            #             sale_order_line.product_uom_qty - sale_order_line.qty_delivered)
            # sale_order.qty_ordered = qty_ordered
            # sale_order.qty_remaining = qty_remaining
            # sale_order.qty_total_remaining = qty_remaining


