from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class RmaPopUp(models.TransientModel):

    _name = 'rma.report.popup'
    _description = "Rma Pop Up"

    #  domain="['|',('state', '=', 'return'),'&', ('picking_ids.state','=','done'),('picking_ids.location_dest_id.name','=','Stock')]"
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)

    def open_table(self):
        if self.sale_order_id.id:
            data_dict = {'sale_order_id' : self.sale_order_id.name,
                         'partner_id' : self.sale_order_id.partner_id.name,
                         'create_date' : self.sale_order_id.create_date,
                         'expire_date': self.sale_order_id.validity_date,
                         'sale_order_status' : self.sale_order_id.state,
                         'amount_total' : self.sale_order_id.amount_total}

            products_list = []

            sale_order_lines = self.env['sale.order.line'].search([('order_id', '=', self.sale_order_id.id)])

            for sale_order_line in sale_order_lines:
                if sale_order_line.product_id.product_tmpl_id.type != 'service':
                    return_qty = 0
                    price_unit = 0
                    price_total = 0
                    umo_name = ''
                    for picking_id in sale_order_line.order_id.picking_ids:
                        if picking_id.location_dest_id.name == 'Stock' and picking_id.state == 'done':
                            for stock_move in picking_id.move_lines:
                                if stock_move.product_id.id == sale_order_line.product_id.id:
                                    price_unit += sale_order_line.product_id.list_price
                                    price_total += (sale_order_line.product_id.list_price * stock_move.product_uom_qty)
                                    umo_name = stock_move.product_uom.name
                                    return_qty += stock_move.product_uom_qty
                    products_list.append([sale_order_line.product_id.product_tmpl_id.name,
                                          sale_order_line.product_id.product_tmpl_id.sku_code,
                                          return_qty,
                                          umo_name,
                                          price_unit,
                                          price_total])

            data_dict.update(dict(moves=products_list))

        action = self.env.ref('rma_report.action_rma_report').report_action([], data=data_dict)
        action.update({'target': 'main'})

        return action

