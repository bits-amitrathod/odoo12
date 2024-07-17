# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductsOnHandByDatePopUp(models.TransientModel):
    _name = 'popup.on_hand_by_date'
    _description = 'On Hand By Date Popup'

    report_date = fields.Date('Report On Date', default=fields.date.today(), required=True)

    costing_method = fields.Selection([
        ('1', 'Standard Costing '),
        ('2', 'Average Costing'),
        ('3', 'FIFO Costing')
    ], string="Costing Method", default='1',
        help="Choose to analyze the Show Summary or from a specific date in the past.")

    vendor_id = fields.Many2one('res.partner', string='Vendor', required=False, )
    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    show_inactive_products = fields.Boolean('Show Active Products', default=True, required=False)
    show_cost = fields.Boolean('Show Cost', default=False, required=False)

    quantities = fields.Selection([
        ('0', 'Show Only with Quantities '),
        ('1', 'Include Zero Quantities '),
        ('2', 'Show Only Zero Quantities ')
    ], string="Quantities", help="", default='0')

    def open_table(self):

        if self.show_cost:
            tree_view_id = self.env.ref('on_hand_by_date.on_hand_by_date_list_view').id
            res_model = 'report.on.hand.by.date.cost'
        else:
            tree_view_id = self.env.ref('on_hand_by_date.on_hand_by_datelist_view').id
            res_model = 'report.on.hand.by.date'

        form_view_id = self.env.ref('on_hand_by_date.on_hand_by_dateform_view').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('On Hand By Date'),
            'res_model': res_model,
            'target': 'main',
            'domain': [('date_order','>=',self.report_date)]
        }

        if self.vendor_id.id:
            action["domain"].append(('partner_id', '=', self.vendor_id.id))

        if self.sku_code:
            action["domain"].append(('product_name', '=', self.sku_code.name))

        if self.quantities == 0:
            action["domain"].append(('qty_done', '>', '0'))
        elif self.quantities == 2:
            action["domain"].append(('qty_done', '=', '0'))

        if self.show_inactive_products:
            action["domain"].append(('is_active', '=', self.show_inactive_products))

        if self.warehouse_id.id:
            action["domain"].append(('warehouse_id', '=', self.warehouse_id.id))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()