# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class MTDReportPopup(models.TransientModel):

    _name = 'mtd_sales.popup'
    _description = 'MTD Popup'

    selected_date = fields.Date('Start Date', default=fields.date.today(), required=True)

    def open_table(self):

        tree_view_id = self.env.ref('mtd_sales.mtd_sales_graph_view').id
        form_view_id = self.env.ref('mtd_sales.mtd_sales_form_view').id

        year = MTDReportPopup.string_to_date(str(self.selected_date)).year
        month = MTDReportPopup.string_to_date(str(self.selected_date)).month

        x_res_model = 'mtd_sales'

        mtd_context = {'year': year, 'month': month }

        self.env[x_res_model].with_context(mtd_context).init_table()

        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'graph')],
            'view_mode': 'graph',
            'name': _('MTD Sales'),
            'res_model': x_res_model,
            'target': 'main',
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()