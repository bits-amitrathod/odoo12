from odoo import api, fields, models ,_
import datetime
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)

class CustomerListPopUp(models.TransientModel):
    _name = 'inventory.customer_price_list_popup'
    _description = 'Inventory Customer Price List PopUp'
    customer_list = fields.Many2one('res.partner',string='Customer',domain="[('active','=',True),('customer','=',True),('is_parent','=',True)]", required=True)
    products = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]" , required=True)
    def open_table(self):
        #print(self.env.ref('inventory__allocation_so.view_inv_all_so_tree').id)
        tree_view_id = self.env.ref('report_price_list.view_inv_all_pricing_rule_customer_tree').id
        form_view_id = self.env.ref('report_price_list.inv_customer_price_list_form').id
        if self.products:
            products=self.env['product.product'].search([('id','=',self.products.id),('product_tmpl_id.type','=','product')])
        else:
            products = []

        margins_context = {'customer_list': self.customer_list,'product_id':products}
        x_res_model = 'inv.customer_price_list'

        self.env[x_res_model].with_context(margins_context).delete_and_create()

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'),(form_view_id,'form')],
            'name': _('Customer Price List'),
            'context': {'group_by': 'customer_name'},
            'res_model': x_res_model,
            'target': 'main'
        }
        # action.update({'target': 'main'})
        return action



class ProductListPopUp(models.TransientModel):
    _name = 'inventory.product_price_list_popup'
    _description = 'Inventory Product Price List PopUp'
    products = fields.Many2one('product.product', string='Product SKU',
                                    domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):
        # print(self.env.ref('inventory__allocation_so.view_inv_all_so_tree').id)
        tree_view_id = self.env.ref('report_price_list.view_inv_all_pricing_rule_product_tree').id
        form_view_id = self.env.ref('product.product_template_form_view').id

        if not self.products:
         products = self.env['product.product'].search([])
         action = {
             'type': 'ir.actions.act_window',
             'view_mode': 'tree,form',
             'views': [(tree_view_id, 'tree'),(form_view_id,'form')],
             'name': _('Product Price List'),
             'res_model': 'product.product',
             'domain':[('active','=',True),('product_tmpl_id.type','=','product')],
             'target': 'main'
         }
        else:
            products=self.products
            action = {
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'views': [(tree_view_id, 'tree'),(form_view_id,'form')],
                'name': _('Product Price List'),
                'res_model': 'product.product',
                'domain': [('id', 'in', [products.id])],
                'target': 'main'
            }



        # action.update({'target': 'main'})
        return action