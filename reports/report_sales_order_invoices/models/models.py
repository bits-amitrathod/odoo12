# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class report_sales_order_invoices(models.TransientModel):
    _name = 'report.sale.order.invoices'
    _description = 'Sales Order Invoice'

    compute_at_date = fields.Selection([
        ('0', 'Show All '),
        ('1', 'Selected '),
        ('2', 'Date Range ')
    ],default='0', string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")
    start_date = fields.Datetime('Start Date', help="Choose report Start date",
                                 default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Datetime('End Date', help="Choose report End date",
                               default=fields.Datetime.now)

    order_invoices = fields.Many2many('account.invoice', domain="[('type','=', 'out_invoice'),('state','=','open')]", string='Invoices')

    def open_table(self):

        tree_view_id = self.env.ref('account.invoice_tree').id
        form_view_id = self.env.ref('account.invoice_form').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'name': _('Sales Order Invoice'),
            'res_model': 'account.invoice',
            # 'context': {'search_default_product': 1},
            'domain': [('type','=', 'out_invoice'),('state','=','open')]
        }

        if self.compute_at_date == '0':

            return action
        elif self.compute_at_date == '1':
            action['domain'].append(('id', 'in', self.order_invoices.ids))
            return action
        elif self.compute_at_date == '2':
            action.update({'domain': [('date_invoice', '>=', self.start_date),
                                      ('date_invoice', '<=', self.end_date),
                                      ('state','=','open')]})
            return action
