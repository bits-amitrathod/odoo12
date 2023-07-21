from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class BdAccountClosedReportPopup_18(models.TransientModel):
    _name = 'popup.bd.account.closed_18'

    start_date = fields.Date('Start Date', default=fields.date.today(), required=True,
                             help="Choose a date to get the Revenue From Accounts Closed In 18 Months By BD at that End date")
    business_development = fields.Many2one('res.users', string='Business Development', index=True)

    delivery_start_date = fields.Date('Revenue Start Date')
    delivery_end_date = fields.Date('Revenue End Date')

    # #@api.multi
    def open_table(self):

        start_date = self.string_to_date(str(self.start_date))
        end_date = start_date - datetime.timedelta(days=365 + (6 * 30))
        end_date_from_first = datetime.date(end_date.year, end_date.month, 1)
        start_date = start_date + datetime.timedelta(days=1)

        tree_view_id = self.env.ref('account_closed_by_bd_18.account_closed_by_bd_list_view_18').id
        form_view_id = self.env.ref('account_closed_by_bd_18.account_closed_by_bd_form_view_18').id
        res_model = 'report.bd.account.closed_18'
        margins_context = {'start_date': start_date, 'end_date': end_date_from_first, 'business_development': self.business_development.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        group_by_domain = ['business_development', 'customer', 'invoice_date:month']

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Revenue From Accounts Closed In 18 Months By BD',
            'res_model': res_model,
            'domain': [],
            'context': {'group_by': group_by_domain}
        }

        if self.delivery_start_date and self.delivery_end_date:
            updated_delivery_end_date = self.string_to_date(str(self.delivery_end_date)) + datetime.timedelta(days=1)
            action['domain'].append(('delivery_date', '>=', self.delivery_start_date))
            action['domain'].append(('delivery_date', '<=', updated_delivery_end_date))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()