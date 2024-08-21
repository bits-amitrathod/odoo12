# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class MarginsReportPopup(models.TransientModel):

    _name = 'margins.popup'
    _description = 'Margins Popup'

    group_by = fields.Selection([
        ('product_id', 'Product '),
        ('partner_id', 'Customer')
    ], string="Group By", default='product_id', required=True, _defaluts = {'field_name' : 'product',})

    customer_id = fields.Many2one('res.partner', string='Customer', required=False, )

    product_id = fields.Many2one('product.product', string='Product', required=False)

    sale_order_id = fields.Many2one('sale.order', string='SO Number', required=False)

    date_range = fields.Selection([
        ('0', 'This Month '),
        ('1', 'Date Range'),
    ], string="Date Range", default='0', help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.date.today())

    end_date = fields.Date('End Date', default=fields.date.today())

    include_returns = fields.Boolean('Include Returns', default=True, required=False)

    include_shipping = fields.Boolean('Include Shipping', default=False, required=False)

    def _valid_field_parameter(self, field, name):
        return name == '_defaluts' or super()._valid_field_parameter(field, name)

    def open_table(self):

        tree_view_id = self.env.ref('margins.margins_list_view').id
        form_view_id = self.env.ref('margins.margins_form_view').id

        if self.date_range:
            s_date = MarginsReportPopup.string_to_date(str(self.start_date))
            e_date = MarginsReportPopup.string_to_date(str(self.end_date))
        else:
            e_date = datetime.date.today()
            s_date = datetime.date.today().replace(day=1)

        margins_context = {'s_date': s_date, 'e_date': e_date, 'include_returns': self.include_returns,
                           'group_by': self.group_by,'include_shipping': self.include_shipping}

        if self.customer_id.id:
            margins_context.update({'partner_id': self.customer_id.id})

        if self.product_id.id:
            margins_context.update({'product_id': self.product_id.id})

        if self.sale_order_id.id:
            margins_context.update({'sale_order_id': self.sale_order_id.id})

        group_by_domain = ['product_id']

        x_res_model = 'margins'


        if self.group_by == 'partner_id':
            group_by_domain.insert(0, 'partner_id')
            x_res_model = 'margins.group_by_cust'
            tree_view_id = self.env.ref('margins.margins_grp_by_cust_list_view').id
        self.env[x_res_model].with_context(margins_context).delete_and_create()


        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Margins'),
            'res_model': x_res_model,
            'context': {'group_by': group_by_domain, 'order_by': group_by_domain},
            'target': 'main',
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
