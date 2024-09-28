# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.tools import float_repr
from odoo import _
from datetime import date
import datetime

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'aging_popup.view.model'
    _description = "Aging popup View Model"

    current_date = date.today()
    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")
    warehouse_id = fields.Many2one('stock.warehouse', 'Group Location',required=True,default=1)
    location_id=fields.Selection(selection=[('Receving', 'Receving'),('Shipping', 'Shipping'), ('Stock', 'Stock'), ], string='Location')



    def open_table(self):
        tree_view_id = self.env.ref('aging_report.aging_report_tree').id
        #form_view_id = self.env.ref('stock.view_production_lot_form').id
        form_view_id = self.env.ref('aging_report.aging_report_form').id
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Pick')]).id
        if not cust_location_id  or  cust_location_id is None:
           cust_location_id = self.env['stock.location'].search([('name', '=', 'Packing Zone')]).id
        stock_location=(self.warehouse_id['lot_stock_id']).id
        receiving_location=(self.warehouse_id['lot_stock_id']).id

        margins_context = {'cust_location_id': cust_location_id,'stock_location':stock_location,'receiving_location':receiving_location}
        x_res_model = 'aging.report'

        self.env[x_res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Aging Report'),
            'res_model': x_res_model,
            'context': {'group_by': 'type'},
            'domain':[('warehouse_id', '=',1)],
            'target': 'main'
        }

        if self.sku_code:
            action["domain"].append(('product_name', 'ilike', self.sku_code.name))

        if self.location_id:
            action["domain"].append(('type', 'ilike', self.location_id))

        return action

