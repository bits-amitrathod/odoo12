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
    shipping_number = fields.Char("Tracking Reference")
    purchase_order = fields.Char()
    def open_table(self):
        tree_view_id = self.env.ref('packing_list.view_inv_all_packing_list_tree').id
        x_res_model = 'stock.picking'
        pull_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
        select_query = """ SELECT  ARRAY_AGG(DISTINCT sp.id) as id 
                      from  stock_picking sp  
                             LEFT JOIN stock_move_line sml ON sml.picking_id=sp.id
                             LEFT JOIN sale_order so ON so.id=sp.sale_id  
                             LEFT JOIN res_partner pr ON pr.id=sp.partner_id 
                             LEFT JOIN sale_order_line sol ON sol.order_id=so.id
                             LEFT JOIN product_product pp ON pp.id=sol.product_id
                             LEFT JOIN product_template pt  ON pt.id=pp.product_tmpl_id 
                      where sp.state='done' and pt.type='product'   """

        if not self.order_number and not self.shipping_number and not self.purchase_order:
            if (self.start_date and self.end_date) or (not self.start_date is None and not self.end_date is None):
                if self.start_date and (not self.start_date is None):
                    start_date = datetime.datetime.strptime(str(self.start_date), "%Y-%m-%d")
                    select_query = select_query + " and sp.write_date >='" + str(start_date) + "'"
                if self.end_date and (not self.end_date is None):
                    end_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d")
                    if (self.start_date and (not self.start_date is None)) and start_date == end_date:
                        end_date = end_date + datetime.timedelta(days=1)
                    select_query = select_query + " and sp.write_date <='" + str(end_date) + "'"
        if self.order_number and not self.order_number is None:
            sale_order = "("
            for sale in self.order_number:
                sale_order = sale_order + str(sale.id) + ","
            sale_order = sale_order[:-1]
            sale_order = sale_order + ")"
            select_query = select_query + """and sp.sale_id in """ + sale_order
        if self.shipping_number:
            select_query = select_query + " and sp.carrier_tracking_ref ='" + str(self.shipping_number) + "'"
        if self.purchase_order:
            select_query = select_query + " and so.client_order_ref ='" + str(self.purchase_order) + "'"
        if pull_location_id:
            select_query = select_query + " and sp.location_dest_id ='" + str(pull_location_id) + "'"
        self._cr.execute(select_query)
        ids = self._cr.fetchall()
        picking_ids=[]
        if ids:
            picking_ids = (ids[0])[0]
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree')],
            'name': _('Packing List'),
            'res_model': x_res_model,
            'domain': [('id', 'in', picking_ids)],
            'target': 'main'
        }
        # action.update({'target': 'main'})
        return action



