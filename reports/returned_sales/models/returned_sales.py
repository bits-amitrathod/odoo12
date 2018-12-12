# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):

    _name = 'returned_sales.popup'
    _description = 'Products On Order'

    compute_at_date = fields.Selection([
        (0, 'All '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.Datetime.now)

    end_date = fields.Date('End Date', default = fields.Datetime.now)

    sale_person_id = fields.Many2one('res.users', string='Sales Person', required=False)

    product_id = fields.Many2one('product.product', string='Product', required=False)

    customer_id = fields.Many2one('res.partner', string='Customer', required=False,)

    def open_table(self):
        tree_view_id = self.env.ref('returned_sales.returned_saleslist_view').id
        form_view_id = self.env.ref('returned_sales.returned_salesform_view').id

        if self.compute_at_date:
            s_date = ProductSaleByCountPopUp.string_to_date(str(self.start_date))
            e_date = ProductSaleByCountPopUp.string_to_date(str(self.end_date))
        else:
            e_date = datetime.date.today()
            s_date = datetime.date.today().replace(day=1)

        returned_sales_context = {}

        if self.customer_id.id:
            returned_sales_context.update({'partner_id': self.customer_id.id})

        if self.product_id.id:
            returned_sales_context.update({'product_id': self.product_id.id})

        if self.sale_person_id.id:
            returned_sales_context.update({'sales_partner_id': self.sale_person_id.id})

        self.env['returned_sales.order'].with_context(returned_sales_context).delete_and_create()

        domain = [('moved_date', '>=', s_date), ('moved_date', '<=', e_date)]

        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Returned Sales'),
            'res_model': 'returned_sales.order',
            'context': {'group_by': 'product_id',},
            'domain' : domain,
            'target': 'main',
        }

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
