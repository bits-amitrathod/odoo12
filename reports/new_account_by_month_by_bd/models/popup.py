from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

class BdNewAccountByMonthReportPopup(models.TransientModel):
    _name = 'popup.bd.new.account'
    _description = "Bd New Account By Month Report Popup"

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)),required=True ,help="Choose a date to get the New Account By Month By Business Development at that  Start date")
    end_date = fields.Date('End Date',default=fields.date.today(),required=True , help="Choose a date to get the New Account By Month By Business Development at that  End date")
    business_development = fields.Many2one('res.users', string="Business Development", index=True)

    # #@api.multi
    def open_table(self):
        e_date = self.string_to_date(str(self.end_date))
        e_date = e_date + datetime.timedelta(days=1)

        tree_view_id = self.env.ref('new_account_by_month_by_bd.new_account_by_month_by_bd_list_view').id
        form_view_id = self.env.ref('new_account_by_month_by_bd.new_account_by_month_by_bd_form_view').id
        res_model = 'report.bd.new.account'
        margins_context = {'start_date': self.start_date, 'end_date': e_date,
                           'business_development': self.business_development.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'New Account By Month By BD',
            'res_model': res_model,
            'context': {'group_by': ('business_development','onboard_date')},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()