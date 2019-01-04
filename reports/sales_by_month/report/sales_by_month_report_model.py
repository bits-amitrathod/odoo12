import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_month.sales_by_month_template'

    @api.model
    def get_report_values(self, docids, data=None):

        records = self.env['sales_by_month'].search([('id', 'in', docids)])

        popup = self.env['salesbymonth.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_date and popup.end_date and not popup.start_date is None and not popup.end_date is None:
            date = datetime.strptime(popup.start_date, '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                popup.end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {
            'data': records,
            'date': date}