import logging
from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

log = logging.getLogger(__name__)


class ReportBdAccountClosed(models.AbstractModel):
    _name = 'report.account_closed_by_bd.bd_account_closed_temp_test'

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['report.bd.account.closed'].browse(docids)

        popup = self.env['popup.bd.account.closed'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.start_date:
            s_date = self.string_to_date(str(popup.start_date))
            e_date = s_date - datetime.timedelta(days=365)

            date = datetime.datetime.strptime(str(s_date), '%Y-%m-%d').strftime(
                '%m/%d/%Y') + " - " + datetime.datetime.strptime(
                str(e_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': records, 'date': date}

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()