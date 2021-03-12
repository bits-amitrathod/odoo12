# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):
    _name = 'popup.sales.by.count'
    _description = 'Sales By Count'

    user_id = fields.Many2one('res.users', 'Business Development')
    # warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    compute_at_date = fields.Selection([
        ('0', 'Show All '),
        ('1', 'Date Range ')
    ], string="Compute", default='0', help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.date.today())

    end_date = fields.Date('End Date', default=fields.date.today())

    def open_table(self):
        tree_view_id = self.env.ref('sales_by_count.report_sales_by_count_list_view').id
        form_view_id = self.env.ref('sales_by_count.report_sales_by_count_form_view').id

        res_model = 'report.sales.by.count'
        margins_context = {'start_date': self.start_date, 'end_date': self.end_date, 'compute_at': self.compute_at_date,
                           'user_id': self.user_id.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Sales By Count',
            'res_model': res_model,
            "context": {"search_default_group_by_location": 1},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
