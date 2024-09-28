from odoo import api, models
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.on_hand_by_expiry.templ'
    _description = "OnHand By Date Report Model"

    def _get_report_values(self, docids, data=None):
        on_hand_by_expiration_date_stock_list = self.env['on_hand_by_expiry'].browse(docids)

        report_date = date.today()

        print(report_date)

        action={
            'report_date': report_date,
            'items': on_hand_by_expiration_date_stock_list,
        }

        return action