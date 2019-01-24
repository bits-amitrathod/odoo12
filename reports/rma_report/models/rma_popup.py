from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class RmaPopUp(models.TransientModel):

    _name = 'rma.report.popup'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True, domain="[('amount_total','<',0), ('state', '=', 'return')]")

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
                    products_list.append([sale_order_line.product_id.product_tmpl_id.name,
                                          sale_order_line.product_id.product_tmpl_id.sku_code,
                                          sale_order_line.product_uom_qty,
                                          sale_order_line.product_uom.name,
                                          sale_order_line.price_unit,
                                          sale_order_line.price_total])

            data_dict.update(dict(moves=products_list))

        action = self.env.ref('rma_report.action_rma_report').report_action([], data=data_dict)
        action.update({'target': 'main'})

        return action

