from odoo import api, fields, models ,_
import datetime

class DiscountSummaryPopUp(models.TransientModel):
    _name = 'compbysale.popup'
    _description = 'Compare Sale By Month'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    current_start_date = fields.Datetime('Current month Start Date', default = (fields.date.today() - datetime.timedelta(days = 31)))
    current_end_date = fields.Datetime('Current month End Date', default = fields.Datetime.now)

    last_start_date = fields.Datetime('Last Month Start Date', default=((fields.date.today() - datetime.timedelta(days=60))))
    last_end_date = fields.Datetime('Last Month End Date', default=(fields.date.today() - datetime.timedelta(days=32)))

    def open_table(self):
        tree_view_id = self.env.ref('report_compare_sale_by_month.list_view').id
        form_view_id = self.env.ref('product.product_normal_form_view').id
        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Compare Sales By Month'),
                'res_model': 'product.product',
                'context': {'current_start_date':self.current_start_date, 'current_end_date':self.current_end_date,
                            'last_start_date': self.last_start_date, 'last_end_date': self.last_end_date},
                'domain': [('type', 'in', ['product'])],
            }
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Compare Sales By Month'),
                'res_model': 'product.product',
                'context': {'current_start_date': self.current_start_date, 'current_end_date': self.current_end_date,
                            'last_start_date': self.last_start_date, 'last_end_date': self.last_end_date},
                'domain': [('type', 'in', ['product'])],
            }
            return action
