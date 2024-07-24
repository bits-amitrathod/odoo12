from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

class BdRevenuePerAccountReportPopup(models.TransientModel):
    _name = 'popup.bd.revenue.per.account'
    _description = "Bd Revenue Per Account Report Popup"

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)), help="Choose a date to get the Revenu By Business Development Per Account at that  Start date")
    end_date = fields.Date('End Date',default=fields.date.today(), help="Choose a date to get the Revenue By Business Development Per Account at that  End date")
    business_development = fields.Many2one('res.users', string="Business Development", index=True)

    compute_at_date = fields.Selection([
        ('0', 'Show All '),
        ('1', 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")


    # #@api.multi
    def open_table(self):
        tree_view_id = self.env.ref('revenue_by_bd_per_account.revenue_by_bd_per_account_list_view').id
        form_view_id = self.env.ref('revenue_by_bd_per_account.revenue_by_bd_per_account_form_view').id
        res_model = 'report.bd.revenue.per.account'
        margins_context = {'start_date': self.start_date, 'end_date': self.end_date, 'compute_at': self.compute_at_date,
                           'business_development': self.business_development.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Revenue By Business Development Per Account',
            'res_model': res_model,
            'context': {'group_by': ('business_development','customer','delivery_date')},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()