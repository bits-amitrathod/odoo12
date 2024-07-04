from odoo import api, fields, models, _
import datetime


class AcquisitionReportPopUp(models.TransientModel):
    _name = 'payments_scheduler.report.summary'
    _description = "Payment Scheduler Report Popup Model"

    end_date = fields.Date('Due Date', help="Choose a date to get the  Invoices at that using  Due date", default=fields.date.today())

    def open_table(self):
        tree_view_id = self.env.ref('payments_scheduler.payment_scheduled_report_list_view').id
        form_view_id = self.env.ref('payments_scheduler.payment_scheduled_report_form_view').id
        end_date = self.end_date
        ai = self.env['account.move'].search([('invoice_date_due','<=', end_date)]).ids

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Payments Scheduled'),
            'res_model': 'account.move',
            'domain': [('move_type', '=', 'in_invoice'),('id', 'in', ai)],
            "context" : {'default_type': 'in_invoice', 'move_type': 'in_invoice','search_default_unpaid': 1}  #, 'journal_type': 'purchase'
        }

        return action
