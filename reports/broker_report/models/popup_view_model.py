from odoo import api, fields, models ,_
import datetime

class BrokerReportPopUp(models.TransientModel):
    _name = 'brokerreport.popup'
    _description = 'Broker Report PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")
    start_date = fields.Datetime('Start Date', help="Choose a date to get the Discount Summary at that  Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Datetime('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default = fields.Datetime.now)

    def open_table(self):

        final_dict = {}

        tree_view_id = self.env.ref('broker_report.broker_form_list').id
        form_view_id = self.env.ref('apprisal_tracker.apprisal_tracker_offer_form').id

        # if self.compute_at_date:
        #     action = {
        #         'type': 'ir.actions.act_window',
        #         'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
        #         'view_mode': 'tree,form',
        #         'name': _('Product Vendor'),
        #         'res_model': 'purchase.order',
        #         'domain': [('confirmation_date','>=', self.start_date ),('confirmation_date','<=', self.end_date ),('state','in',('purchase','done'))],
        #     }
        #     return action
        # else:
        #     action = {
        #         'type': 'ir.actions.act_window',
        #         'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
        #         'view_mode': 'tree,form',
        #         'name': _('Product Vendor'),
        #         'res_model': 'purchase.order',
        #         'domain': [('state', 'in', ('purchase', 'done'))],
        #     }
        #     return action

        action=self.env.ref('broker_report.action_report_broker_report').report_action([], data={})
        action.update({'target':'main'})
        return action
