# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductsOnHandByDatePopUp(models.TransientModel):
    _name = 'popup.on_hand_by_date'
    _description = 'On Hand By Date Popup'

    report_date = fields.Date('Report On Date', default=fields.Datetime.now, required=True)

    costing_method = fields.Selection([
        (1, 'Standard Costing '),
        (2, 'Average Costing'),
        (3, 'FIFO Costing')
    ], string="Costing Method", default=1,
        help="Choose to analyze the Show Summary or from a specific date in the past.")

    vendor_id = fields.Many2one('res.partner', string='Vendor', required=False, )
    product_id = fields.Many2one('product.product', string='Product', required=False)
    location_id = fields.Many2one('stock.location', string='Location', required=False)
    show_inactive_products = fields.Boolean('Show Active Products', default=True, required=False)
    show_cost = fields.Boolean('Show Cost', default=False, required=False)

    quantities = fields.Selection([
        (0, 'Show Only with Quantities '),
        (1, 'Include Zero Quantities '),
        (2, 'Show Only Zero Quantities ')
    ], string="Quantities", help="", default=0)

    def open_table(self):

        if self.show_cost:
            tree_view_id = self.env.ref('on_hand_by_date.on_hand_by_date_list_view').id
        else:
            tree_view_id = self.env.ref('on_hand_by_date.on_hand_by_datelist_view').id

        form_view_id = self.env.ref('on_hand_by_date.on_hand_by_dateform_view').id

        on_hand_by_date_context = {'report_date': self.report_date}

        if self.vendor_id.id:
            on_hand_by_date_context.update({'partner_id': self.vendor_id.id})

        if self.product_id.id:
            on_hand_by_date_context.update({'product_id': self.product_id.id})

        if self.location_id.id:
            on_hand_by_date_context.update({'location_id': self.location_id.id})

        on_hand_by_date_context.update({'show_cost': self.show_cost})
        on_hand_by_date_context.update({'quantities': self.quantities})
        on_hand_by_date_context.update({'product_inactive': self.show_inactive_products})
        on_hand_by_date_context.update({'costing_method': self.costing_method})

        self.env["report.on.hand.by.date"].with_context(on_hand_by_date_context).delete_and_create()

        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('On Hand By Date'),
            'res_model': 'report.on.hand.by.date',
            'target': 'main',
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
