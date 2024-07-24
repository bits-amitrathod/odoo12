# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class VoidedProductPopup(models.TransientModel):

    _name = 'voided.product.popup'
    _description = 'Voided Product Filter'

    compute_at_product_selection = fields.Selection([
        ('0', 'All Voided Products[Products not in SPS Inventory]'),
        ('1', 'All Unprocessed Products[Low/Out of stock products at the time of request]')
    ], string="Products", default='0', help="Choose Voided Products which are not in inventory or Unprocessed Products "
                                         "which were not allocated because of some reason")

    compute_at_date = fields.Selection([
        ('0', 'Show All'),
        ('1', 'Date Range ')
    ], string="Compute", default='0', help="Choose Show All or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.date.today())

    end_date = fields.Date('End Date', default=fields.date.today())

    customer_id = fields.Many2one('res.partner', string='Customer', required=False,)

    def open_table(self):
        """
        Opens a window with a tree and form view of 'sps.customer.requests' model.
        The window is filtered based on the user's selections in the popup window.

        Returns:
            dict: A dictionary containing the action parameters for opening the window.
        """
        # Get the IDs of the tree and form views for 'ps.customer.requests' model
        tree_view_id = self.env.ref('customer-requests.view_tree_voided_products').id
        form_view_id = self.env.ref('customer-requests.view_form_voided_product').id

        domain = [('status', '=', 'Unprocessed')] if self.compute_at_product_selection == '1' else [('status', '=', 'Voided')]

        if self.compute_at_date == '1':
            s_date = self.string_to_date(str(self.start_date))
            e_date = self.string_to_date(str(self.end_date)) # + datetime.timedelta(days=1)
            domain.append(('create_date', '>=', s_date))
            domain.append(('create_date', '<=', e_date))

        if self.customer_id.id:
            domain.append(('customer_id', '=', self.customer_id.id))

        # Define the action parameters for opening the window
        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Voided Product'),
            'res_model': 'sps.customer.requests',
            # 'context': {'group_by': 'customer_id',},
            'domain': domain,
            'target': 'main',
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()