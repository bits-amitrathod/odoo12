from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

class KaRevenueReportPopup(models.TransientModel):
    _name = 'popup.ka.revenue'

    start_date = fields.Date('Start Date', help="Choose a date to get the Revenu By Key Account at that  Start date",
                                 default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Revenue By Key Account at that  End date",
                               default=fields.date.today())
    key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
                                                                            "('share','=',False)]")

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")


    # @api.multi
    def open_table(self):
        tree_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_list_view').id
        form_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_form_view').id
        res_model = 'report.ka.revenue'
        margins_context = {'start_date': self.start_date, 'end_date': self.end_date, 'compute_at': self.compute_at_date,
                           'key_account': self.key_account.id}
        self.env[res_model].with_context(margins_context).delete_and_create()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Revenue By Key Account',
            'res_model': res_model,
            'context': {'group_by': 'key_account'},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()