from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api
import datetime
_logger = logging.getLogger(__name__)




class ProductTemplate(models.Model):
    _inherit = 'product.template'
    max_inventory_level = fields.Char("Max Inv Level",compute='_compute_max_inventory_level')
    max_inventory_percent= fields.Char("Current % of Max Inv Level",compute='_compute_max_inventory_level')
    qty_in_stock = fields.Char("Qty In Stock",compute='_compute_max_inventory_level')
    qty_on_order=fields.Char("Qty On Order",compute='_compute_max_inventory_level')
    max_inventory_future_percent = fields.Char("Future % of Max Inv Level", compute='_compute_max_inventory_level')
    inventory_percent_color=fields.Integer("Inv Percent Color", compute='_compute_max_inventory_level')
    future_percent_color = fields.Integer("Inv Percent Color", compute='_compute_max_inventory_level')
    inventory_monitor=fields.Boolean("Can be Monitored")
    max_inventory_product_level_duration = fields.Integer(string="Max Inventory Level",store=True,default=0)

    def _compute_max_inventory_level(self):
        params = self.env['ir.config_parameter'].sudo()
        max_inventory_level_duration = int(params.get_param('inventory_monitor.max_inventory_level_duration'))
        today_date = datetime.datetime.now()
        #final_month = fields.Date.to_string(today_date - datetime.timedelta(days=max_inventory_level_duration))
        last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
        for ml in self:
            location_ids = self.env['stock.location'].search([('usage', '=', 'internal'), ('active', '=', True)])
            cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            if ml.max_inventory_product_level_duration is not None and ml.max_inventory_product_level_duration > 0 :
                max_inventory_level_duration = int(ml.max_inventory_product_level_duration)
            quantity = 0
            sale_quant = 0
            purchase_qty = 0
            max_inventory = 0
            products = self.env['product.product'].search([('product_tmpl_id', '=', ml.id),('qty_available','>=',0)])
            for product_id in products:
                self.env.cr.execute(
                    "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON sp.sale_id=sol.id LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND sml.location_dest_id =%s AND sml.product_id =%s AND sp.date_done>=%s",
                    (cust_location_id,product_id.id, last_3_months))
                quant = self.env.cr.fetchone()
                if quant[0] is not None and max_inventory_level_duration>0:
                    sale_quant = sale_quant + int(quant[0])
                    #max_inventory=int(((sale_quant)*30)/max_inventory_level_duration)
                    avg_sale_quant = float(sale_quant/3)
                    max_inventory = int((avg_sale_quant) * float(max_inventory_level_duration/30))
                    ml.max_inventory_level =str(float(max_inventory))
                if  product_id.incoming_qty:
                    purchase_qty=purchase_qty+int(product_id.incoming_qty)
                quantity = int(product_id.qty_available) + int(quantity)
            ml.qty_on_order= str(purchase_qty)


            ml.qty_in_stock = str(int(quantity))
            if max_inventory>0:
                max_inventory_percent = (quantity/int(max_inventory))*100
                ml.max_inventory_level = str(int(max_inventory))
                ml.max_inventory_percent= "" +str(int(max_inventory_percent))+"%"

                inventory_future_percent =((purchase_qty + ml.actual_quantity)/int(max_inventory))*100
                ml.inventory_percent_color =int(max_inventory_percent)
                ml.future_percent_color=int(inventory_future_percent)
                ml.max_inventory_future_percent="" +str(int(inventory_future_percent))+"%"
            else:
                ml.max_inventory_percent="0%"
                ml.max_inventory_future_percent="0%"
                ml.max_inventory_level = "0"
                ml.inventory_percent_color=0
                ml.future_percent_color=0

    @api.model_cr
    def init(self):
        print("init")

    @api.model_cr
    def delete_and_create(self):
        print("delete_and_create")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    max_inventory_level=fields.Boolean("Max Inventory Level")
    max_inventory_level_duration = fields.Integer(string="Duration")


    @api.onchange('max_inventory_level_duration')
    def _onchange_max_inventory_level_duration(self):
        if self.max_inventory_level_duration > 365:
            self.max_inventory_level_duration = 0

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        production_lot_alert_days = int(params.get_param('inventory_extension.production_lot_alert_days'))
        production_lot_alert_settings = params.get_param('inventory_extension.production_lot_alert_settings',
                                                         default=True)
        group_stock_production_lot = params.get_param('inventory_extension.group_stock_production_lot')
        module_product_expiry = params.get_param('inventory_extension.module_product_expiry')
        max_inventory_level=params.get_param('inventory_monitor.max_inventory_level')
        max_inventory_level_duration=int(params.get_param('inventory_monitor.max_inventory_level_duration'))
        _logger.info("max inventory level :%r" ,max_inventory_level_duration)
        res.update(production_lot_alert_settings=production_lot_alert_settings,
                   production_lot_alert_days=production_lot_alert_days,
                   max_inventory_level=max_inventory_level,
                   max_inventory_level_duration=max_inventory_level_duration,
                   group_stock_production_lot=group_stock_production_lot,
                   module_product_expiry=module_product_expiry)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.production_lot_alert_days",
                                                         self.production_lot_alert_days)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.production_lot_alert_settings",
                                                         self.production_lot_alert_settings)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.group_stock_production_lot",
                                                         self.group_stock_production_lot)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.module_product_expiry",
                                                         self.module_product_expiry)
        self.env['ir.config_parameter'].sudo().set_param("inventory_monitor.max_inventory_level",
                                                         self.max_inventory_level)
        self.env['ir.config_parameter'].sudo().set_param("inventory_monitor.max_inventory_level_duration",
                                                         self.max_inventory_level_duration)


class ReportInventoryMonitor(models.AbstractModel):
    _name = 'report.inventory_monitor.inventory_monitor_print'
    @api.model
    def get_report_values(self, docids, data=None):
         _logger.info("print report called...")
         monitor=self.env['inventory.monitor1'].browse(docids)
         return {'data': monitor}


class ProductTemplate(models.Model):
    _name = 'inventory.monitor1'

    max_inventory_level = fields.Integer("Max Inv Level", default="0")
    max_inventory_percent= fields.Integer("Current % of Max Inv Level", default="0")
    qty_in_stock = fields.Integer("Qty In Stock")
    type = fields.Selection( [('product', 'Stockable Product'),('consu', 'Consumable'), ('service', 'Service')] , string="Type")
    sku_code = fields.Char("SKU / Catalog No")
    max_inventory_future_percent = fields.Integer("Future % of Max Inv Level", default="0")
    inventory_percent_color=fields.Integer("Inv Percent Color", default="0")
    future_percent_color = fields.Integer("Inv Percent Color", default="0")
    qty_on_order = fields.Integer("Qty On Order")

    inventory_monitor=fields.Boolean("Can be Monitored")
    max_inventory_product_level_duration = fields.Integer(string="Max Inventory Level")
    product_tmpl_id = fields.Many2one('product.template', "Product Template")
    product_id = fields.Many2one('product.product', "Product Name")
    actual_quantity = fields.Integer("Actual Quantity ")


    def _compute_max_inventory_level(self,max_inventory_level_duration,today_date,last_3_months,cust_location_id,ml):

        if ml.product_tmpl_id.max_inventory_product_level_duration is not None and ml.product_tmpl_id.max_inventory_product_level_duration > 0 :
            max_inventory_level_duration = int(ml.product_tmpl_id.max_inventory_product_level_duration)
        quantity = 0
        sale_quant = 0
        purchase_qty = 0
        max_inventory = 0
        product_id = ml.product_id
        quant = self.get_quant(cust_location_id,product_id, last_3_months)
        if quant is not None and max_inventory_level_duration>0:
            sale_quant = sale_quant + int(quant)
            avg_sale_quant = float(sale_quant/3)
            max_inventory = int((avg_sale_quant) * float(max_inventory_level_duration/30))
            ml.max_inventory_level =  int(max_inventory)
        if  product_id.incoming_qty:
            purchase_qty=purchase_qty+int(product_id.incoming_qty)

        quantity = int(product_id.qty_available) + int(quantity)
        ml.qty_on_order= int(purchase_qty)
        ml.qty_in_stock =  int(quantity)
        ml.type = ml.product_tmpl_id.type
        ml.sku_code = ml.product_tmpl_id.sku_code

        if max_inventory>0:
            max_inventory_percent = (quantity/int(max_inventory))*100
            inventory_future_percent =((purchase_qty + ml.actual_quantity)/int(max_inventory))*100

            ml.max_inventory_percent =  int(max_inventory_percent)
            ml.max_inventory_future_percent= int(inventory_future_percent)
            ml.max_inventory_level =  int(max_inventory)
            ml.inventory_percent_color = int(max_inventory_percent)
            ml.future_percent_color = int(inventory_future_percent)



    def action_your_report(self):
        print("action_your_report")
        self.init_table()
        tree_view_id = self.env.ref('inventory_monitor.view_inventory_moniter_line_tree_test').id
        form_view_id = self.env.ref('inventory_monitor.view_inventory_moniter_line_form_test').id

        sql = "INSERT INTO inventory_monitor1 (product_tmpl_id , max_inventory_product_level_duration ,actual_quantity ,inventory_monitor,product_id ,max_inventory_level ,max_inventory_percent ,max_inventory_future_percent , inventory_percent_color ,future_percent_color )SELECT product_template.id as product_tmpl_id, max_inventory_product_level_duration, actual_quantity,inventory_monitor ,product_product.id as product_id , '0' as max_inventory_level ,'0' as max_inventory_percent , '0' as max_inventory_future_percent , '0' as inventory_percent_color, '0' as future_percent_color FROM product_template left join product_product ON product_product.product_tmpl_id =  product_template.id where inventory_monitor = true "
        self._cr.execute(sql)

        max_inventory_level_duration = self.get_max_inventory_level_duration()

        today_date = datetime.datetime.now()
        last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id

        list = self.env['inventory.monitor1'].search([]).sudo()
        for ml in list :
            self._compute_max_inventory_level(max_inventory_level_duration,today_date,last_3_months,cust_location_id,ml)

        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": 'inventory.monitor1',
            "name": "inventory monitor ",
            'views': [(tree_view_id, 'tree'),(form_view_id,'form')],
        }
        return action

    def init_table(self):
        sql_query = """ 
                    DELETE FROM inventory_monitor1
                """
        self._cr.execute(sql_query)

    def get_max_inventory_level_duration(self):
        params = self.env['ir.config_parameter'].sudo()
        max_inventory_level_duration = int(params.get_param('inventory_monitor.max_inventory_level_duration'))
        return max_inventory_level_duration

    def get_quant(self,cust_location_id,product_id , last_3_months):
        self.env.cr.execute(
            "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON sp.sale_id=sol.id LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND sml.location_dest_id =%s AND sml.product_id =%s AND sp.date_done>=%s",
            (cust_location_id, product_id.id, last_3_months))
        quant = self.env.cr.fetchone()
        return quant[0]