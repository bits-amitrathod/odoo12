from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TrendingReport(models.TransientModel):
    _name = 'popup.trending.report'
    _description = 'Trending Report 6 and 12 month'

    start_date = fields.Date('Start Date', required=True)
    code = fields.Char()

    def open_table(self):
        self.code = self.env.context['code']

        if(self.env.context['code'] == 12):
            tree_view_id = self.env.ref('trending_report.trending_report_list12').id
            form_view_id = self.env.ref('base.view_partner_form').id
            end_date = self.start_date - datetime.timedelta(days=366)
        else:
            tree_view_id = self.env.ref('trending_report.trending_report_list6').id
            form_view_id = self.env.ref('base.view_partner_form').id
            end_date = self.start_date - datetime.timedelta(days=185)

        sale_orders = self.env['sale.order'].\
            search(
            [
                ('state', 'in', ['sale']),
                ('date_order', '<=', self.start_date),
                ('date_order', '>=', end_date)
            ])

        partner_list = sale_orders.partner_id
        res_model = 'res.partner'
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': 'Trending Report',
            'res_model': res_model,
            'context': {'search_default_customer': 1,'s_date': self.start_date,'trending_report':True},
            'domain': [('id', 'in', partner_list.ids)],
            'search_view_id': self.env.ref('base.view_res_partner_filter').id,
        }

        return action