# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
from odoo.exceptions import ValidationError
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductsOnHandByExpiryPopUp(models.TransientModel):

    _name = 'on_hand_by_expiry.popup'
    _description = 'On Hand By Expiration Popup'

    date_range = fields.Selection([
        ('0', 'This Month '),
        ('1', 'Date Range'),
    ], string="Date Range", default='0', help="Choose to analyze the Show Summary or from a specific date in the past.")

    state = fields.Selection([
        ('0', 'All'),
        ('1', 'Expired'),
        ('2', 'Expiring'),
        ('3', 'Valid'),
    ], string="Status", default='0',)

    warehouse_id = fields.Many2one('stock.warehouse', 'Group Location', required=True, default=1)
    location_id = fields.Selection(selection=[('lot_stock_id', 'Pick'), ('wh_pack_stock_loc_id', 'Pack'), ('wh_output_stock_loc_id', 'Ship')], string='Location')
    start_date = fields.Date('Start Date', default=fields.date.today())
    end_date = fields.Date('End Date', default=fields.date.today())
    sku_code =  fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")


    def open_table(self):
        tree_view_id = self.env.ref('on_hand_by_expiry.on_hand_by_expiry_list_view').id
        form_view_id = self.env.ref('on_hand_by_expiry.on_hand_by_expiryform_view').id

        on_hand_by_expiry_context = {}
        domain = []

        if self.date_range == '1':
            s_date = ProductsOnHandByExpiryPopUp.string_to_date(str(self.start_date))
            e_date = ProductsOnHandByExpiryPopUp.string_to_date(str(self.end_date))
            if s_date > e_date:
                raise ValidationError("Start date should eariler then end date")
        else:
            e_date = False
            s_date = False

        on_hand_by_expiry_context.update({'s_date' : s_date,'e_date' : e_date})

        locations = []
        if self.warehouse_id and not self.warehouse_id is None:
            if self.location_id:
                location_id = self.warehouse_id[self.location_id]
                if location_id:
                    locations.append(location_id.id)
            else:
                lot_stock_id = self.warehouse_id['lot_stock_id']
                locations.append(lot_stock_id.id)
                if self.warehouse_id['wh_pack_stock_loc_id']:
                    wh_pack_stock_loc_id = self.warehouse_id['wh_pack_stock_loc_id']
                    locations.append(wh_pack_stock_loc_id.id)
                if self.warehouse_id['wh_output_stock_loc_id']:
                    wh_output_stock_loc_id = self.warehouse_id['wh_output_stock_loc_id']
                    locations.append(wh_output_stock_loc_id.id)
        on_hand_by_expiry_context.update({'locations': locations})

        self.env['on_hand_by_expiry'].with_context(on_hand_by_expiry_context).delete_and_create()

        if self.state:
            switcher = {
                0: "All",
                1: "Expired",
                2: "Expiring",
                3: 'Valid'
            }
            filter_state = switcher.get(self.state, False)
            if filter_state:
                print('filter_state value : ',str(filter_state))
                domain.append(('status', '=', str(filter_state)))

        action= {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('On Hand By Expiration'),
            'res_model': 'on_hand_by_expiry',
            'target': 'main',
            'domain' : domain

        }

        if self.sku_code:
            action["domain"].append(('product_id.id', '=', self.sku_code.id))

        if self.warehouse_id:
           action["domain"].append(('warehouse_id', '=', self.warehouse_id.id))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()