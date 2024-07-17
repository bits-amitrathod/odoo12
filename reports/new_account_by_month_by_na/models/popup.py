from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

class NaNewAccountByMonthReportPopup(models.TransientModel):
    _name = 'popup.na.new.account'
    _description = "Na New Account By Month Report Popup"

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)), required=True, help="Choose a date to get the New Account By Month By National Account at that  Start date")
    end_date = fields.Date('End Date', default=fields.date.today(), required=True, help="Choose a date to get the New Account By Month By National Account at that  End date")
    national_account = fields.Many2one('res.users', string="National Account", index=True)

    # #@api.multi
    def open_table(self):
        e_date = self.string_to_date(str(self.end_date))
        e_date = e_date + datetime.timedelta(days=1)

        tree_view_id = self.env.ref('new_account_by_month_by_na.new_account_by_month_by_na_list_view').id
        form_view_id = self.env.ref('new_account_by_month_by_na.new_account_by_month_by_na_form_view').id
        res_model = 'report.na.new.account'
        margins_context = {'start_date': self.start_date, 'end_date': e_date,
                           'national_account': self.national_account.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'New Account By Month By NA',
            'res_model': res_model,
            'context': {'group_by': ('national_account','onboard_date')},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()