# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductsSoldByBdPopUp(models.TransientModel):
    _name = 'popup.product.sold.by.bd'
    _description = 'Short date and over stocked product sold by BD'

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', default=fields.date.today())
    # key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
    #                                                                         "('share','=',False)]")
    business_development = fields.Many2one('res.users', 'Business Development', domain="[('active', '=', True)]")

    compute_at_date = fields.Selection([
        ('0', 'Show All '),
        ('1', 'Date Range ')
    ], string="Compute", default='0', help="Choose to analyze the Show Summary or from a specific date in the past.")

    def open_table(self):
        tree_view_id = self.env.ref('stocked_product_sold_by_bd.report_product_sold_by_bd_list_view').id
        form_view_id = self.env.ref('stocked_product_sold_by_bd.report_product_sold_by_bd_form_view').id

        res_model = 'report.product.sold.by.bd'
        margins_context = {'start_date': self.start_date, 'end_date': self.end_date, 'compute_at': self.compute_at_date,
                           'business_development': self.business_development.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Short date and over stocked product sold by BD',
            'res_model': res_model,
            # 'context': {'group_by': 'key_account', },
            # "context": {"search_default_group_by_location": 1},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
