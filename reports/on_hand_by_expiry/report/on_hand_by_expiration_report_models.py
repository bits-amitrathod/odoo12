from odoo import api, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.on_hand_by_expiry.templ'

    @api.model
    def get_report_values(self, docids, data=None):
        on_hand_by_expiration_date_stock_list = self.env['on_hand_by_expiry'].browse(docids)

        report_date = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        data_dict = dict(items=on_hand_by_expiration_date_stock_list,report_date=report_date)

        action = self.env.ref('on_hand_by_expiry.action_report_on_hand_by_expiry').report_action([],
                                            data=data_dict)
        action.update({'target': 'main'})

        return action