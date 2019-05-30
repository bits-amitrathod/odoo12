from odoo import api, fields, models, _
import datetime


class  AcquisitionReportPopUp(models.TransientModel):
    _name = 'payments_scheduler.report.summary'
    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date",
                                 default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date",
                               default=fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('payments_scheduler.form_list').id
        form_view_id = self.env.ref('payments_scheduler.form_view').id

        ai = self.env['account.invoice'].search([('date_invoice','>=',self.start_date),('date_invoice','<=',self.end_date)]).ids

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Payments Scheduled'),
            'res_model': 'account.invoice',
            'domain': [('type', '=', 'in_invoice'),('id', 'in', ai)],
            "context" : {'default_type': 'in_invoice', 'type': 'in_invoice'}  #, 'journal_type': 'purchase'
        }

        return action
