from odoo import api, fields, models ,_
import datetime

class DiscountSummaryPopUp(models.TransientModel):
    _name = 'discountsummary.popup'
    _description = 'Discount Summary PopUp'
    _auto = False

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")
    start_date = fields.Datetime('Start Date', help="Choose a date to get the Discount Summary at that  Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Datetime('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default = fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('report_discount_summary.form_list').id
        form_view_id = self.env.ref('sale.view_order_form').id
        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Discount Summary'),
                'res_model': 'sale.order',
                'domain': [('confirmation_date','>=', self.start_date ),('confirmation_date','<=', self.end_date ),('state','in',('sale','done'))],
            }
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Discount Summary'),
                'res_model': 'sale.order',
                'domain': [('state', 'in', ('sale', 'done'))],
            }
            return action
