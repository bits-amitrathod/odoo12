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
    current_date = date.today()
    sku_code = fields.Char('Product SKU')
    warehouse_id = fields.Many2one('stock.warehouse', 'Group Location',required=True,default=1)
    location_id=fields.Selection(selection=[('wh_pack_stock_loc_id', 'Pick'), ('wh_output_stock_loc_id', 'Pack'), ('customer', 'Ship')], String='Location')



    def open_table(self):
        tree_view_id = self.env.ref('aging_report.aging_report_tree').id
        #form_view_id = self.env.ref('stock.view_production_lot_form').id
        form_view_id = self.env.ref('aging_report.aging_report_form').id
        locations=[]
        if self.warehouse_id and not self.warehouse_id is None:
            if self.location_id:
                if self.location_id == 'customer':
                    location_id = self.env['stock.location'].search([('name', '=', 'Customers')])
                else:
                    location_id=self.warehouse_id[self.location_id]
                if location_id:
                    locations.append(location_id.id)
            else:
                lot_stock_id = self.env['stock.location'].search([('name', '=', 'Customers')])
                locations.append(lot_stock_id.id)
                if self.warehouse_id['wh_pack_stock_loc_id']:
                    wh_pack_stock_loc_id=self.warehouse_id['wh_pack_stock_loc_id']
                    locations.append(wh_pack_stock_loc_id.id)
                if self.warehouse_id['wh_output_stock_loc_id']:
                    wh_output_stock_loc_id=self.warehouse_id['wh_output_stock_loc_id']
                    locations.append(wh_output_stock_loc_id.id)
        margins_context = {'locations': locations}
        x_res_model = 'aging.report'

        self.env[x_res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Aging Report'),
            'res_model': x_res_model,
            'context': {'group_by': 'location_id'},
            'domain':[('use_date', '>=',self.current_date)],
            'target': 'main'
        }

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code))

        if self.warehouse_id:
           action["domain"].append(('warehouse_id', '=', self.warehouse_id.id))


        return action

