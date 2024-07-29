import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)

class ReportNaNewAccount(models.AbstractModel):
    _name = 'report.new_account_by_month_by_na.na_new_account_temp_test'
    _description = "Report Na New Account"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.na.new.account'].browse(docids)

        popup = self.env['popup.na.new.account'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_date and popup.end_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime(
                '%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'accounts': records, 'date': date}

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
