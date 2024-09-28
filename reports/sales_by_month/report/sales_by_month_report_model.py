import logging
from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_month.sales_by_month_template'
    _description = 'Report Product Sale By Count'

    @api.model
    def _get_report_values(self, docids, data=None):

        records = self.env['product.product'].search([('id', 'in', docids)])
        popup = self.env['salesbymonth.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        today = datetime.date(datetime.strptime(str(popup.end_date), "%Y-%m-%d"))
        end_of_month = today + relativedelta(day=1,months=1, days=-1)
        sixth_month = (today - relativedelta(day=1, months=5))

        if popup.end_date and not popup.end_date is None:
            date = sixth_month.strftime('%m/%d/%Y') + " - " + end_of_month.strftime('%m/%d/%Y')
        else:
            date = False
        month6=(today - relativedelta(months=5)).strftime('%b-%Y')
        month5 = (today - relativedelta(months=4)).strftime('%b-%Y')
        month4 = (today - relativedelta(months=3)).strftime('%b-%Y')
        month3 = (today - relativedelta(months=2)).strftime('%b-%Y')
        month2 = (today - relativedelta(months=1)).strftime('%b-%Y')
        month1 = (today).strftime('%b-%Y')
        return {
            'data': records,
            'date': date,
            'month1':month1,
            'month2':month2,
            'month3':month3,
            'month4':month4,
            'month5':month5,
            'month6' :month6
        }