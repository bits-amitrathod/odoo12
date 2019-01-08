from odoo import api, fields, models ,_
import datetime

class ProductVendorListPopUp(models.TransientModel):
    _name = 'popup.product.vendor.list'
    _description = 'Product Vendor List PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.",default=0)
    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date", default = (fields.date.today() - datetime.timedelta(days = 31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default = fields.Datetime.now)
    product_id = fields.Many2one('product.product', string='Product', required=False)

    def open_table(self):
        tree_view_id = self.env.ref('product_vendor_list.vendor_form_list').id
        form_view_id = self.env.ref('purchase.purchase_order_form').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Product Vendor List'),
            'res_model': 'purchase.order',
            'domain': [('state', 'in', ('purchase', 'done'))],
            'target': 'main'
        }

        if self.compute_at_date:
            if self.start_date:
                action["domain"].append(('date_order', '>=', self.start_date))

            if self.end_date:
                action["domain"].append(('date_order', '<=', self.end_date))

        if self.product_id.id:
            action['domain'].append(('order_line', 'in', self.product_id.id))

        return action

