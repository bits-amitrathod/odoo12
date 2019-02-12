# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging

_logger = logging.getLogger(__name__)


class PickingReportPopUp(models.TransientModel):

    _name = 'pick_report.popup'
    _description = 'Pick Report Popup'

    picking_id = fields.Many2one('stock.picking', string='Pick Number', required=True, domain=[('state', '!=', 'cancel')])

    def open_table(self):
        location_group=""
        carrier_id=""
        if self.picking_id.picking_type_id.warehouse_id:
            location_group=self.picking_id.picking_type_id.warehouse_id.code
        if self.picking_id.carrier_id:
            carrier_id = self.picking_id.carrier_id.name
        data_dict = {'scheduled_date': self.picking_id.scheduled_date,
                     'priority': self.picking_id.priority,
                     'state': self.picking_id.state.capitalize(),
                     'type': self.picking_id.picking_type_id.name,
                     'location_group':location_group,
                     'carrier_id':carrier_id
                     }

        if self.picking_id.sale_id.id:
            data_dict.update({'order_id': self.picking_id.sale_id.name})
            data_dict.update({'partner_name': self.picking_id.sale_id.partner_id.name})
        else:
            data_dict.update({'order_id': '', 'partner_name': ''})

        products_list = []

        moves = self.env['stock.move.line'].search([('picking_id', '=', self.picking_id.id)])

        for stock_move in moves:
            products_list.append([stock_move.state, stock_move.ordered_qty,
                                  [str(
                                      stock_move.product_id.product_tmpl_id.sku_code) + " - " + stock_move.product_id.product_tmpl_id.name,
                                   stock_move.lot_id.name, str(stock_move.lot_id.use_date)],
                                  stock_move.location_id.complete_name,
                                  stock_move.reference,
                                  stock_move.location_dest_id.complete_name
                                 ])

        data_dict.update(dict(moves=products_list))

        action = self.env.ref('pick_report.action_pick_report').report_action([], data=data_dict)
        action.update({'target': 'main'})

        return action
