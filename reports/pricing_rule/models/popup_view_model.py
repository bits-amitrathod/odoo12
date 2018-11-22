from odoo import api, fields, models ,_
import datetime
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)

class TrendingReportListPopUp(models.TransientModel):
    _name = 'inventory.pricing_rules_popup'
    _description = 'Inventory Allocation Report List PopUp'
    partner_id = fields.Many2many('res.partner',string='Customers', required=True)
    product_id= fields.Many2many('product.product',string='Products', required=True)
    def open_table(self):
        #print(self.env.ref('inventory__allocation_so.view_inv_all_so_tree').id)
        tree_view_id = self.env.ref('pricing_rule.view_inv_all_pricing_rule_tree').id
        # form_view_id = self.env.ref('pricing_rule.inv_sale_order_form_view')



        margins_context = {'partner_id': self.partner_id,'product_id':self.product_id}
        group_by_domain = ['customer_name']
        x_res_model = 'res.pricing_rule'

        self.env[x_res_model].with_context(margins_context).delete_and_create()

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree')],
            'name': _('Inventory Pricing Rule'),
            'context': {'group_by': group_by_domain, 'order_by': group_by_domain},
            'res_model': x_res_model,
            'target': 'main'
        }
        # action.update({'target': 'main'})
        return action



