# # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class SpsReceivingList(models.Model):
    _inherit = 'stock.move.line'

    sku_code = fields.Char('Product SKU', store=False, compute="_get_sku")
    qty_rece = fields.Float('Qty Received', store=False, compute="_get_sku",digits='Product Unit of Measure')
    date_done = fields.Datetime('Date Validated', store=False, compute="_get_sku")
    purchase_order_id = fields.Char('Purchase Order', store=False, compute="_get_sku")
    purchase_partner_id = fields.Char('Vendor', store=False, compute="_get_sku")
    # carrier_info = fields.Integer('Carrier Info', store=False, compute="_get_sku")
    # date_order = fields.Datetime("Order Date", store=False, compute="_get_sku")
    exp_date = fields.Datetime('Expired Date', store=False, compute="_get_sku")


    #@api.multi
    def _get_sku(self):
        for move_line in self:
            if move_line.product_id:
                purchase_order_id = move_line.move_id.purchase_line_id.order_id
                move_line.update({
                    'sku_code' :  move_line.product_id.sku_code,
                    'qty_rece' : move_line.qty_done,
                    'date_done' : move_line.picking_id.date_done,
                    'purchase_order_id': purchase_order_id.name ,
                    'purchase_partner_id': purchase_order_id.partner_id.name,
                    'exp_date' : move_line.lot_id.use_date
                    # 'carrier_info': purchase_order_id.carrier_info,
                    # 'date_order': purchase_order_id.date_order,
                })

class receivingList(models.Model):
    _inherit = "stock.picking"

    def do_sps_receiving_list(self):
        print("Ok.........")
        # return self.env['sps_receive_popup.view.model'].open_table()
        # action = self.env["ir.actions.actions"]._for_xml_id("sps_receiving_list_report.action_sps_receive_list")
        # tree_view_id = self.env.ref('sps_receiving_list_report.form_list_sps').id
        # form_view_id = self.env.ref('sps_receiving_list_report.sps_receving_list_form').id
        # stock_location_id = self.env['stock.location'].search([('name', '=', 'Stock')]).ids
        # print("Stock location id", stock_location_id)
        # action = {
        #     'type': 'ir.actions.act_window',
        #     'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
        #     'view_mode': 'tree',
        #     # 'name': _('SPS Receiving List'),
        #     'res_model': 'stock.move.line',
        #     'domain': [('state', '=', 'done'), ('location_dest_id.id', '=', stock_location_id)],
        #     'context': {"search_default_product_group": 1},
        #     # 'target': 'main'
        # }
        # action['domain'].append(('move_id.purchase_line_id.order_id', 'in', [9992]))

        return self.env.ref('sps_receiving_list_report.action_sps_receiving_list_report_pdf').report_action(self.move_line_ids)
        # return action