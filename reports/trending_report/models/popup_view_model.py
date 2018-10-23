from odoo import api, fields, models ,_
import datetime

class TrendingReportListPopUp(models.TransientModel):
    _name = 'trendingreportlist.popup'
    _description = 'Trending Report List PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.",default=0)
    start_date = fields.Datetime('Start Date', help="Choose a date to get the Discount Summary at that  Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Datetime('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default = fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('trending_report.trending_report_list').id
        # form_view_id = self.env.ref('product_vendor_list.product_vendor_list_form').id
        form_view_id = self.env.ref('base.view_partner_form').id

        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Trending Report List'),
                'res_model': 'res.partner',
                # 'domain': [('date_order','>=', self.start_date ),('date_order','<=', self.end_date ),('state','in',('sale','done'))],
                'target': 'main'
            }
            # action.update({'target': 'main'})
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Trending Report List'),
                'res_model': 'res.partner',
                # 'domain': [('state', 'in', ('sale', 'done'))],
                'target': 'main'
            }

            # action.update({'target': 'main'})
            return action

