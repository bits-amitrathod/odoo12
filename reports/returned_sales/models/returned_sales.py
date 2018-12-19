# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):

    _name = 'popup.returned.sales'
    _description = 'Products On Order'

    compute_at_date = fields.Selection([
        (0, 'All '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.Datetime.now)

    end_date = fields.Date('End Date', default = fields.Datetime.now)

    sale_person_id = fields.Many2one('res.users', string='Sales Person', required=False)

    sku_code = fields.Char('SKU / Catalog No')

    customer_id = fields.Many2one('res.partner', string='Customer', required=False,)

    def open_table(self):
        tree_view_id = self.env.ref('returned_sales.returned_saleslist_view').id
        form_view_id = self.env.ref('returned_sales.returned_salesform_view').id

        self.env['report.returned.sales.order'].delete_and_create()

        action =  {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Returned Sales'),
            'res_model': 'report.returned.sales.order',
            'context': {'group_by': 'product_id',},
            'domain' :  [],
            'target': 'main',
        }

        if self.customer_id.id:
            action["domain"].append(('partner_id', '=', self.customer_id.id))

        if self.sale_person_id.id:
            action["domain"].append(('user_id', '=', self.sale_person_id.id))

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code))

        if self.compute_at_date:
            if self.start_date:
                action["domain"].append(('moved_date', '>=', self.start_date))

            if self.end_date:
                action["domain"].append(('moved_date', '<=', self.end_date))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


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
