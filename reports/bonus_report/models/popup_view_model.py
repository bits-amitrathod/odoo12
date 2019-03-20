from odoo import api, fields, models ,_
import datetime

class BonusReportPopUp(models.TransientModel):
    _name = 'bonusreport.popup'
    _description = 'Bonus Report PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.",default=0)
    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default = fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('bonus_report.bonus_form_list').id
        form_view_id = self.env.ref('appraisal_tracker.appraisal_tracker_offer_form').id

        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Bonus Report'),
                'res_model': 'purchase.order',
                'context' : {'vendor_offer_data': True},
                'domain': [('date_order','>=', self.start_date ),('date_order','<=', self.end_date ),('state','in',('purchase','purchase')),('status', 'in', ('purchase', 'purchase'))],
                'target': 'main'
            }
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Bonus Report'),
                'res_model': 'purchase.order',
                'context': {'vendor_offer_data': True},
                'domain': [('state', 'in', ('purchase', 'purchase')),('status', 'in', ('purchase', 'purchase'))],
                'target': 'main'
            }
            return action

