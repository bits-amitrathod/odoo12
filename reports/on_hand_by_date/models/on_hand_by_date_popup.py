# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductsOnHandByDatePopUp(models.TransientModel):

    _name = 'on_hand_by_date.popup'
    _description = 'On Hand By Date Popup'

    report_date = fields.Datetime('Report On Date', default=fields.Datetime.now, required=True)

    costing_method = fields.Selection([
        (0, 'Average Cost '),
        (1, 'FIFO ')
    ], string="Costing Method", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    vendor_id = fields.Many2one('res.partner', string='Vendor', required=False, )

    product_id = fields.Many2one('product.product', string='Product', required=False)

    show_inactive_products = fields.Boolean('Show Inactive Products', default=True, required=False)

    include_zero_quanities = fields.Boolean('Include Zero Quantities', default=False, required=False)

    show_cost = fields.Boolean('Show Cost', default=False, required=False)

    show_only_zero_quantities = fields.Boolean('Show Only Zero Quantities', default=False, required=False)

    def open_table(self):

        tree_view_id = self.env.ref('on_hand_by_date.on_hand_by_datelist_view').id
        form_view_id = self.env.ref('on_hand_by_date.on_hand_by_dateform_view').id

        on_hand_by_date_context = {'report_date': self.report_date}

        if self.vendor_id.id:
            on_hand_by_date_context.update({'partner_id': self.vendor_id.id})

        if self.product_id.id:
            on_hand_by_date_context.update({'product_id': self.product_id.id})

        self.env['on_hand_by_date.stock'].with_context(on_hand_by_date_context).delete_and_create()

        domain = [('product_id.active', '=', True)]

        if self.show_inactive_products:
            domain.clear()

        if self.show_only_zero_quantities:
            domain.append(('qty_on_hand', '=', 0))
        else:
            if self.include_zero_quanities:
                domain.append(('qty_on_hand', '>=', 0))
            else:
                domain.append(('qty_on_hand', '>', 0))

        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('On Hand By Date'),
            'res_model': 'on_hand_by_date.stock',
            'domain' : domain,
            'target': 'main',
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


class ResPartnerExtension(models.Model):
    _inherit = 'res.users'

    sales_person = fields.Integer(default=0, compute='_check_sales_person', store=True)


    @api.multi
    def _check_sales_person(self):
        for record in self:
            if record.sale_team_id and record.sale_team_id.team_type == 'sales':
                record.sales_person = 1
            else:
                record.sales_person = 0
