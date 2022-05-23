from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class NewAccountBonusReportPopup(models.TransientModel):
    _name = 'popup.new.account.bonus.report'

    start_date = fields.Date('Start Date', default=fields.date.today(), required=True,
                             help="Choose a date to get the New Account Bonus Report at that Start date")

    business_development = fields.Many2one('res.users', string="Business Development", index=True,
                                           domain="['|', ('active', '=', True), ('active', '=', False)]")

    key_account = fields.Many2one('res.users', string="Key Account", index=True,
                                  domain="['|', ('active', '=', True), ('active', '=', False)]")

    # @api.multi
    def open_table(self):
        start_date = self.string_to_date(str(self.start_date))
        end_date = start_date - datetime.timedelta(days=365)
        end_date_13 = start_date - datetime.timedelta(days=396)
        end_date_13_12months = end_date_13 + datetime.timedelta(days=365)
        # start_date = start_date + datetime.timedelta(days=1)

        tree_view_id = self.env.ref('new_account_bonus_report.new_account_bonus_report_list_view').id
        form_view_id = self.env.ref('new_account_bonus_report.new_account_bonus_report_form_view').id
        res_model = 'new.account.bonus.report'
        margins_context = {'start_date': start_date, 'end_date': end_date,'end_date_13': end_date_13,
                           'end_date_13_12months': end_date_13_12months,
                           'business_development': self.business_development.id,
                           'key_account': self.key_account.id}

        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'New Account Bonus Report',
            'res_model': res_model,
            'context': {'group_by': 'customer'},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()