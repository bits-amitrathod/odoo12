# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
import datetime
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'sps_receive_popup.view.model'
    _description = 'sps receive popup view model'

    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")
    purchase_order = fields.Many2many('purchase.order', string="Receiving",domain="[('state','=','purchase')]",)

    compute_at_date = fields.Selection([
        ('0', 'Show All'),
        ('1', 'Date Range'),
        ('2', 'Receiving')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")

    def open_table(self):
        tree_view_id = self.env.ref('sps_receiving_list_report.form_list_sps').id
        form_view_id = self.env.ref('sps_receiving_list_report.sps_receving_list_form').id
        stock_location_id = self.env['stock.location'].search([('name', '=', 'Stock')]).ids
        print("Stock location id", stock_location_id)
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree',
            'name': _('SPS Receiving List'),
            'res_model': 'stock.move.line',
            'domain': [('state', '=', 'done'),('location_dest_id.id', '=', stock_location_id)],
            'context': {"search_default_product_group": 1},
            'target': 'main'
        }

        if self.compute_at_date=='1':
            if self.end_date:
                e_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d")
                e_date = str(e_date + datetime.timedelta(days=1))
                action['domain'].append(('date', '<=', e_date))

            if self.start_date:
                action['domain'].append(('date', '>=', self.start_date))

            action['domain'].append(('move_id.purchase_line_id', '!=', False))
            return action
        elif self.compute_at_date == '2':
            print('--------------------')
            print(self.purchase_order.ids)
            print(len(self.purchase_order.ids))
            if(len(self.purchase_order.ids)>0):
                action['domain'].append(('move_id.purchase_line_id.order_id', 'in', self.purchase_order.ids))
            else:
                action['domain'].append(('move_id.purchase_line_id', '!=', False))
            return action
        else:
            action['domain'].append(('move_id.purchase_line_id', '!=', False))
            action['domain'].append(('move_id.to_refund', '=', False))
            return action