# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime


class report_sales_order_invoices(models.TransientModel):
    _name = 'report.sale.order.invoices'
    _description = 'Sales Order Invoice'

    compute_at_date = fields.Selection([
        ('0', 'By Date Range '),
        ('1', 'By Sales Order ')
    ], default='0', string="Compute", help="")

    start_date = fields.Date('Start Date', help="Choose report Start date",
                             default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', help="Choose report End date",
                           default=fields.date.today())

    sale_order = fields.Many2one('sale.order', string='Sales Order')

    def open_table(self):

        tree_view_id = self.env.ref('account.view_invoice_tree').id
        # form_view_id = self.env.ref('account.view_move_form').id
        records = self.env['sale.order'].search([])
        list = records.mapped('name')

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')], #, (form_view_id, 'form')
            'view_type': 'form',
            'view_mode': 'tree,form',
            'name': _('Sales Order Invoice'),
            'res_model': 'account.move',
            'context': {'search_default_product': 1}
        }

        if self.compute_at_date == '0':
            action['domain'] = [('state', '=', 'open'), ('invoice_date', '>=', self.start_date),
                                ('invoice_date', '<=', self.end_date),
                                ('invoice_origin', 'in', list)
                                ]
            return action
        elif self.compute_at_date == '1':
            action['domain'] = [
                ('invoice_origin', '=', self.env['sale.order'].search([('id', '=', self.sale_order.ids[0])])[0].name),
                ('state', '=', 'open')]
            return action