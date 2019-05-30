from odoo import api, fields, models, _
import datetime


class  AcquisitionReportPopUp(models.TransientModel):
    _name = 'payments_scheduler.report.summary'

    end_date = fields.Date('Due Date', help="Choose a date to get the  Invoices at that using  Due date",
                               default=fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('payments_scheduler.form_list').id
        form_view_id = self.env.ref('payments_scheduler.form_view').id

        ai = self.env['account.invoice'].search([('date_invoice','<=',self.end_date)]).ids

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Payments Scheduled'),
            'res_model': 'account.invoice',
            'domain': [('type', '=', 'in_invoice'),('id', 'in', ai)],
            "context" : {'default_type': 'in_invoice', 'type': 'in_invoice','search_default_unpaid': 1}  #, 'journal_type': 'purchase'
        }

        return action
