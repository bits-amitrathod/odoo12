from odoo import api, fields, models ,_
import datetime
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)

class TrendingReportListPopUp(models.TransientModel):
    _name = 'sale.packing_list_popup'
    _description = 'Sale Packing List'

    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date")
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date")
    order_number = fields.Many2many('sale.order', string="Sale Order")
    shipping_number = fields.Char()
    purchase_order = fields.Char()
    def open_table(self):
        tree_view_id = self.env.ref('packing_list.view_inv_all_packing_list_tree').id
        margins_context = {'start_date': self.start_date,'end_date':self.end_date,'sale_number':self.order_number,'shipping_number':self.shipping_number,'purchase_order':self.purchase_order}
        group_by_domain = ['name']
        x_res_model = 'res.stock_packing_list'

        self.env[x_res_model].with_context(margins_context).delete_and_create()

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree')],
            'name': _('Inventory Packing List'),
            'res_model': x_res_model,
            'target': 'main'
        }
        # action.update({'target': 'main'})
        return action



