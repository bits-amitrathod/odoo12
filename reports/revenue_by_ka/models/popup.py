from odoo import api, fields, models,_
import datetime
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class KaRevenueReportPopup(models.TransientModel):
    _name = 'popup.ka.revenue'

    start_date = fields.Date('Start Date', default=fields.date.today(),
                             help="Choose a date to get the Selected month report", required=True)
    key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
                                                                            "('share','=',False)]")

    # @api.multi
    def open_table(self):
        start_date_month = datetime.datetime(self.start_date.year, self.start_date.month, 1)
        end_date_month = datetime.datetime(self.start_date.year, self.start_date.month, calendar.mdays[self.start_date.month])
        tree_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_list_view').id
        form_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_form_view').id
        res_model = 'report.ka.revenue'
        margins_context = {'start_date': start_date_month, 'end_date': end_date_month, 'key_account': self.key_account.id}

        self.env[res_model].with_context(margins_context).delete_and_create()

        group_by_domain = ['key_account']

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Revenue By Key Account',
            'res_model': res_model,
            'context': {'group_by': group_by_domain},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()