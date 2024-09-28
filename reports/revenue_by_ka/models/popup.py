from odoo import api, fields, models,_
import datetime
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from dateutil import relativedelta


class KaRevenueReportPopup(models.TransientModel):
    _name = 'popup.ka.revenue'
    _description = 'Ka Revenue Report Popup'

    start_month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                    ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                    ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Start Month', required=True)

    start_year = fields.Selection([(str(num), str(num)) for num in range(2010, (datetime.datetime.now().year) + 20)],
                                  'Start Year', default=str(datetime.datetime.now().year), required=True)

    end_month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                 ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                 ('10', 'October'), ('11', 'November'), ('12', 'December')], 'End Month', required=True)

    end_year = fields.Selection([(str(num), str(num)) for num in range(2010, (datetime.datetime.now().year) + 20)],
                                'End Year', default=str(datetime.datetime.now().year), required=True)

    key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
                                                                            "('share','=',False)]")

    # #@api.multi
    def open_table(self):
        start_date = datetime.datetime.strptime(str(self.start_year) + "-" + str(self.start_month) + "-01", "%Y-%m-%d").date()

        end_date_custom = datetime.datetime.strptime(str(self.end_year) + "-" + str(self.end_month) + "-15", "%Y-%m-%d")

        end_date = datetime.datetime(end_date_custom.year, end_date_custom.month, calendar.mdays[end_date_custom.month]).date()

        date_difference = relativedelta.relativedelta(end_date, start_date)
        year_difference = date_difference.years
        add_months = 0
        if year_difference > 0:
            add_months = year_difference * 12
        date_difference = date_difference.months + add_months + 1

        tree_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_list_view').id
        graph_view_id = self.env.ref('revenue_by_ka.revenue_ka_graph_view').id
        pivot_view_id = self.env.ref('revenue_by_ka.revenue_ka_pivot_view').id
        dashboard_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_dashboard_view').id
        form_view_id = self.env.ref('revenue_by_ka.revenue_by_ka_form_view').id
        res_model = 'report.ka.revenue'
        margins_context = {'start_date': start_date, 'end_date': end_date, 'key_account': self.key_account.id,
                           'date_difference': date_difference}

        self.env['report.ka.revenue'].with_context(margins_context).delete_and_create()

        group_by_domain = ['key_account']

        action = {
            'type': 'ir.actions.act_window',
            'views': [(dashboard_view_id, 'dashboard'), (tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'dashboard, tree, form',
            'name': 'Revenue By Key Account',
            'res_model': res_model,
            'context': {'group_by': group_by_domain},
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()