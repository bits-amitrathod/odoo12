# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):

    _name = 'receiving_list.popup'
    _description = 'Receiving List Popup'

    order_type = fields.Selection([
        (1, 'PO'),
        (2, 'SO'),
    ], string="Order Type", default=1, help="Choose to analyze the Show Summary or from a specific date in the past.", required=True)

    sale_order_id = fields.Many2one('sale.order', string='Order Number', )

    purchase_order_id = fields.Many2one('purchase.order', string='Order Number',)

    customer_id = fields.Many2one('res.partner', string='Customer')

    vendor_id = fields.Many2one('res.partner', string='Vendor', )

    purchase_order_id_with_filter = fields.Many2one('purchase.order', string='Order Number',)

    show_with_filter = fields.Integer(string='Show', compute='_show_order_id_with_filter', default=0)

    show_sales_with_filter = fields.Integer(string='Show', compute='_show_sale_order_id_with_filter', default=0)

    sale_order_id_with_filter = fields.Many2one('sale.order', string='Order Number', )

    def open_table(self):
        if self.order_type == 1:
            if self.show_with_filter:
                record = self.purchase_order_id_with_filter
            else:
                record = self.purchase_order_id
            data = self._format_purchase_order_data(record)
        else:
            if self.show_sales_with_filter:
                record = self.sale_order_id_with_filter
            else:
                record = self.sale_order_id
            data = self._format_sale_order_data(record)

        datas = {
            'ids': self,
            'form': data,
            'model': self._name
        }
        action = self.env.ref('receiving_list.action_report_receiving_list').report_action([], data=datas)
        action.update({'target': 'main'})

        return action

    def _format_purchase_order_data(self, purchase_order):
        response = {'order_id': purchase_order.name, 'name': purchase_order.partner_id.display_name,
                    'state': purchase_order.state, 'type': 'Purchase'}
        lines = []
        for line in purchase_order.order_line:
            lines.append([line.product_id.product_tmpl_id.sku_code, line.product_id.product_tmpl_id.name,
                          line.product_qty - line.qty_received, line.qty_received])

        response.update({'lines': lines})

        return response

    def _format_sale_order_data(self, sales_order):
        response = {'order_id': sales_order.name, 'name': sales_order.partner_id.display_name,
                    'state': sales_order.state, 'type': 'Sales'}
        lines = []
        for line in sales_order.order_line:
            sql_query = """
                     SELECT SUM(l.product_qty) as qty_to_receive, SUM(l.qty_done) as qty_received FROM stock_move_line l INNER JOIN stock_move m 
                     ON l.move_id = m.id WHERE m.sale_line_id = """ + str(line.id) + """ AND m.state IN ('assigned', 'done') AND m.origin_returned_move_id IS NOT NULL 
                     """
            self._cr.execute(sql_query)
            moves = self._cr.fetchall()
            qty_to_receive = moves[0][0]
            received_qty = moves[0][1]
            if not qty_to_receive is None and not received_qty is None:
                lines.append([line.product_id.product_tmpl_id.sku_code, line.product_id.product_tmpl_id.name,
                              qty_to_receive, received_qty])
        #     qty_to_receive = received_qty = 0
        #     return_move_found = False
        #     for stock_move in line.move_ids:
        #         if stock_move.origin_returned_move_id and not stock_move.scrapped and stock_move.state != 'cancel':
        #             return_move_found = True
        #             for move_line in stock_move.move_line_ids:
        #                 qty_to_receive = qty_to_receive + move_line.product_qty
        #                 received_qty = received_qty + move_line.qty_done
        #
        #     if return_move_found:
        #         lines.append([line.product_id.product_tmpl_id.sku_code, line.product_id.product_tmpl_id.name,
        #                       qty_to_receive, received_qty])
        response.update({'lines': lines})

        return response

    @api.multi
    @api.depends('vendor_id')
    @api.onchange('vendor_id')
    def _show_order_id_with_filter(self):
        for record in self:
            if record.vendor_id.id is False:
                record.show_with_filter = 0
            else:
                record.show_with_filter = 1

    @api.multi
    @api.depends('customer_id')
    @api.onchange('customer_id')
    def _show_sale_order_id_with_filter(self):
        for record in self:
            if record.customer_id.id is False:
                record.show_sales_with_filter = 0
            else:
                record.show_sales_with_filter = 1


    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


# class SaleOrderLineExt(models.Model):
#     _inherit = "sale.order.line"
#
#     move_ids = fields.One2many('stock.move', 'sale_line_id', string='Moves')



