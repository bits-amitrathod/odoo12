import logging
from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

log = logging.getLogger(__name__)


class NewAccountBonusReport(models.AbstractModel):
    _name = 'report.new_account_bonus_report.new_account_bonus_report_test'
    _description = "New Account Bonus Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        print('In _get_report_values')
        records = self.env['new.account.bonus.report'].browse(docids)

        popup = self.env['popup.new.account.bonus.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        # if popup.start_date and popup.end_date:
        #     date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime(
        #         '%m/%d/%Y') + " - " + datetime.strptime(
        #         str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        # else:
        #     date = False

        print('records')
        print(records)
        return {'accounts': records, 'date': False}

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
