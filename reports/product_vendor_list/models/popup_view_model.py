from odoo import api, fields, models ,_
import datetime

class ProductVendorListPopUp(models.TransientModel):
    _name = 'popup.product.vendor.list'
    _description = 'Product Vendor List PopUp'

    product_id = fields.Many2one('product.product', string='Product', required=True)

    def open_table(self):
        tree_view_id = self.env.ref('product_vendor_list.vendor_form_list').id
        form_view_id = self.env.ref('product_vendor_list.product_vendor_list_report_form').id
        purchase_orders=self.env['purchase.order'].search([('state', 'in', ('purchase', 'done')),('order_line.product_id','=',self.product_id.id)]).sorted(key=lambda r: r.id)
        purc_id={}
        for purchase_order in purchase_orders:
            for order_line in purchase_order.order_line:
                purc_id[str(purchase_order.partner_id.id)+"-"+str(order_line.product_id.id)]=purchase_order.id
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Product Vendor List'),
            'res_model': 'purchase.order',
            'domain': [('state', 'in', ('purchase', 'done')),('id','in',list(purc_id.values()))],
            'target': 'main'
        }



        return action

