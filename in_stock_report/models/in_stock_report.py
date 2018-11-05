from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api
import datetime
_logger = logging.getLogger(__name__)




class ProductTemplate(models.Model):
    _inherit = 'product.product'

    qty_in_stock = fields.Char("Qty In Stock",compute='_compute_max_inventory_level')
    minExDate = fields.Date("Min Expiration Date", compute='_compute_max_inventory_level')
    maxExDate = fields.Date("Max Expiration Date", compute='_compute_max_inventory_level')
    manufacturer=fields.Char("Manufacturer", compute='_compute_max_inventory_level')
    product_name = fields.Char("Product Name", compute='_compute_max_inventory_level')
    product_code = fields.Char("Product Code", compute='_compute_max_inventory_level')
    product_price=fields.Monetary(string='Price Per Unit', currency_field='currency_id', compute = '_compute_max_inventory_level', store=False)
    product_price_symbol = fields.Char(string='Price/Unit',
                                    compute='_compute_max_inventory_level', store=False)
    currency_id = fields.Many2one('res.currency', 'Currency',compute = '_compute_max_inventory_level', store=False)
    sku_reference = fields.Char('SKU / Catalog No',compute = '_compute_max_inventory_level')



    def _compute_max_inventory_level(self):
        for ml in self:
            location_ids = self.env['stock.location'].search([('usage', '=', 'internal'), ('active', '=', True)])
            self.env.cr.execute(
                "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = %s",
                ( ml.id,))
            query_result = self.env.cr.dictfetchone()
            ml.minExDate=fields.Date.from_string(query_result['min'])
            ml.maxExDate =fields.Date.from_string(query_result['max'])
            self.env.cr.execute(
                "SELECT pt.name AS product_name,pt.company_id AS company_id,pt.sku_code AS sku_code,pb.name AS product_manufacturer,pp.default_code AS product_code FROM product_product AS pp "
                "LEFT JOIN product_template AS pt ON pt.id=pp.product_tmpl_id LEFT JOIN product_brand AS pb ON pb.id=pt.product_brand_id where pp.id = %s",
                (ml.id,))
            query_product = self.env.cr.dictfetchone()
            ml.product_name = query_product['product_name']
            ml.manufacturer = query_product['product_manufacturer']
            ml.product_code = query_product['product_code']
            ml.sku_reference = query_product['sku_code']
            company_id = query_product['company_id']
            company = self.env['res.company'].search(
                [('id', '=', company_id)])
            main_company = self.env['res.company'].sudo().search([], limit=1, order="id")
            ml.currency_id = company.sudo().currency_id.id or main_company.currency_id.id
            quantity = 0
            for location_id in location_ids:
                self.env.cr.execute("SELECT sum(quantity) FROM stock_quant WHERE lot_id>%s AND location_id=%s AND product_id=%s AND quantity>%s",(0,location_id.id,ml.id,0))
                total_quant = self.env.cr.fetchone()
                if total_quant[0] is not None:
                    quantity = int(total_quant[0]) + int(quantity)
            ml.qty_in_stock = str(int(quantity))
            ml.product_price=str(ml.lst_price)
            ml.product_price_symbol=ml.check_isAvailable(ml.currency_id['symbol']) +" "+str(ml.lst_price)

    def check_isAvailable(self, value):
        if value:
            return str(value)
        return ""







class TrendingReport(models.AbstractModel):
    _name = 'report.in_stock_report.in_stock_report_print'
    @api.model
    def get_report_values(self, docids, data=None):
         _logger.info("print report called...")
         return {'data': self.env['product.product'].browse(docids)}
