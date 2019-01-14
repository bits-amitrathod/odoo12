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
        (0, 'This Month '),
        (1, 'Date Range'),
    ], string="Date Range", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    state = fields.Selection([
        (0, 'All'),
        (1, 'Expired'),
        (2, 'Expiring'),
        (3, 'Valid'),
    ], string="Status", default=0,)

    location_id = fields.Many2one('stock.location', string='Location', required=False,)

    # product_id = fields.Many2one('product.product', string='Product', required=False)

    start_date = fields.Date('Start Date', default=fields.Datetime.now)

    end_date = fields.Date('End Date', default=fields.Datetime.now)

    product_sku = fields.Char(string="Product SKU")

    def open_table(self):

        tree_view_id = self.env.ref('on_hand_by_expiry.on_hand_by_expiry_list_view').id
        form_view_id = self.env.ref('on_hand_by_expiry.on_hand_by_expiryform_view').id

        domain = []

        if self.date_range:
            s_date = ProductsOnHandByExpiryPopUp.string_to_date(str(self.start_date))
            e_date = ProductsOnHandByExpiryPopUp.string_to_date(str(self.end_date))
            if s_date > e_date:
                raise ValidationError("Start date should eariler then end date")
        else:
            e_date = False
            s_date = False

        on_hand_by_expiry_context = {
            's_date' : s_date,
            'e_date' : e_date
        }

        if self.location_id.id:
            on_hand_by_expiry_context.update({'location_id' : self.location_id.id})

        # if self.product_id.id:
        #     on_hand_by_expiry_context.update({'product_id' : self.product_id.id})

        if self.product_sku:
            on_hand_by_expiry_context.update({'product_sku' : self.product_sku})

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

        group_by_domain = ['location_id']
        action= {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('On Hand By Expiration'),
            'context': {'group_by': group_by_domain, 'order_by': group_by_domain},
            'res_model': 'on_hand_by_expiry',
            'target': 'main',
            'domain' : domain

        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
