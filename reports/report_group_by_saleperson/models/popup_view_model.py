from odoo import api, fields, models ,_
import datetime

class DiscountSummaryPopUp(models.TransientModel):
    _name = 'popup.gross.sales.by.person'
    _description = 'Gross Sale By Business Development'

    compute_at_date = fields.Selection([
        ('0', 'Show All '),
        ('1', 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Date('End Date', default = fields.date.today())

    def open_table(self):

        tree_view_id = self.env.ref('report_group_by_saleperson.view_order_tree').id
        form_view_id = self.env.ref('sale.view_order_form').id

        if self.compute_at_date =='1':
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Gross Sales By Business Development'),
                'res_model': 'sale.order',
                'context': {'group_by':'user_id' , 'start_date' : self.start_date , 'end_date' : self.end_date} ,
                'domain':[('state', '=', 'sale'),('date_order', '>=', self.start_date),('date_order','<=', self.end_date)] ,
            }
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Gross Sales By Business Development'),
                'res_model': 'sale.order',
                'context': {'group_by':'user_id'},
                'domain': [('state', '=', 'sale')],
            }
            return action
