from odoo import api, fields, models ,_
import datetime
from odoo import http
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)

class InventoryAvailabilityPopUp(models.TransientModel):
    _name = 'inventory_availability_popup'
    _description = 'Inventory Availability PopUp'
    location_group = fields.Many2one('stock.warehouse',string='Location Group',domain="[('active','=',True)]")
    products = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")
    def open_table(self):
        #print(self.env.ref('inventory__allocation_so.view_inv_all_so_tree').id)
        tree_view_id = self.env.ref('inventory_availability.view_inventory_availability_line_tree').id
        form_view_id = self.env.ref('stock.product_template_form_view_procurement_button').id
        location_group=self.location_group
        product_ids = []

        if not self.products and location_group:
            list=[]
            list.append(location_group.view_location_id.id)
            list.append(location_group.lot_stock_id.id)
            if location_group.wh_input_stock_loc_id:
                list.append(location_group.wh_input_stock_loc_id.id)
            if location_group.wh_qc_stock_loc_id:
                list.append(location_group.wh_qc_stock_loc_id.id)
            if location_group.wh_output_stock_loc_id:
                list.append(location_group.wh_output_stock_loc_id.id)
            if location_group.wh_pack_stock_loc_id:
                list.append(location_group.wh_pack_stock_loc_id.id)

            stock_quant=  """ select ARRAY(SELECT
                DISTINCT
                product_id
                    FROM
                    stock_quant
                    where
                    location_id in """ + str(tuple(list)) +""" 
                
                ORDER
                BY
                product_id);"""
            self._cr.execute(stock_quant)
            products=self._cr.fetchone()
            if products and products[0]:
                product_ids = products[0]
        elif  self.products:
            product_ids.append(self.products.id)
        else:
             product_ids=self.env['product.product'].search([]).ids
        x_res_model = 'product.product'
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'),(form_view_id,'form')],
            'name': _('Inventory Availability'),
            'domain': [('id', 'in', product_ids)],
            'res_model': x_res_model,
            'target': 'main'
        }
        # action.update({'target': 'main'})
        return action

