# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__
                            )

class ProductSaleByCountPopUp(models.TransientModel):
    _name = 'dormant_customers.popup'
    _description = 'Dormant Customers'

    compute_at_date = fields.Selection([
        (0, 'Last 1 Month '),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Datetime('Start Date', default=fields.Datetime.now)

    end_date = fields.Datetime('End Date', default = fields.Datetime.now)



    def open_table(self):
        tree_view_id = self.env.ref('dormant_customers_report.list_view').id
        form_view_id = self.env.ref('base.view_partner_form').id

        if self.compute_at_date:
            s_date = ProductSaleByCountPopUp.string_to_date(str(self.start_date))
            e_date = ProductSaleByCountPopUp.string_to_date(str(self.end_date))
        else:
            cur_date_time_string = str(datetime.datetime.now())
            try:
                cur_date_time_string = cur_date_time_string[:cur_date_time_string.index('.')]
            except ValueError:
                _logger.info('ok')
            e_date = ProductSaleByCountPopUp.string_to_date(cur_date_time_string)
            s_date = e_date - datetime.timedelta(365/12)

        sale_orders = self.env['sale.order'].search([])

        filtered_sale_orders = list(filter(
            lambda x: x.confirmation_date and \
                      s_date <= ProductSaleByCountPopUp.string_to_date(x.confirmation_date) <= e_date, sale_orders))

        non_domrant_partner_ids_within_selected_date_range = [sale_order.partner_id.id for sale_order in
                                                              filtered_sale_orders]

        all_partners = self.env['res.partner'].search(
            [('customer', '=', True), ('id', 'not in', non_domrant_partner_ids_within_selected_date_range)])

        partner_ids = [partner.id for partner in all_partners if
                       not partner.last_purchase_date or ProductSaleByCountPopUp.string_to_date(
                           str(partner.last_purchase_date)) < e_date]

        partner_ids = list(set(partner_ids))

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Dormant Customers'),
            'res_model': 'res.partner',
            'domain': [('id', 'in', partner_ids)],
            'target': 'main'
        }
        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATETIME_FORMAT).date()

