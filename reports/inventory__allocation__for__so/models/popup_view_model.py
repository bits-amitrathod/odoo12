from odoo import api, fields, models ,_
import datetime

class TrendingReportListPopUp(models.TransientModel):
    _name = 'inventoryforsolist.popup'
    _description = 'Inventory Allocation Report List PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.",default=0)
    start_date = fields.Datetime('Start Date', help="Choose a date to get the Discount Summary at that  Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Datetime('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default = fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('inventory_allocation_for_so.inv_allow_for_so_list').id
        # form_view_id = self.env.ref('product_vendor_list.product_vendor_list_form').id
        form_view_id = self.env.ref('sale.view_order_form').id

        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Inventory Allocation For SO'),
                'res_model': 'sale.order',
                # 'domain': [('date_order','>=', self.start_date ),('date_order','<=', self.end_date ),('state','in',('sale','done'))],
                'target': 'main'
            }
            # action.update({'target': 'main'})
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Inventory Allocation For SO'),
                'res_model': 'sale.order',
                # 'domain': [('state', 'in', ('sale', 'done'))],
                'target': 'main'
            }

            # action.update({'target': 'main'})
            return action

