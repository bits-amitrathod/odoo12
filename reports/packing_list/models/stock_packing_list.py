from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api

_logger = logging.getLogger(__name__)
import datetime

class PricingRule(models.Model):
    _inherit="stock.picking"


    def _compute_picking_vals1(self):
        if self.sale_id.carrier_id:
           return self.sale_id.carrier_id.name
        else:
            return

    def _compute_picking_vals2(self):
        for picking in self:
            if picking.sale_id:
                if picking.sale_id.shipping_terms:
                    picking.shipping_terms = picking.shipping_term(picking.sale_id.shipping_terms)

    shipping_terms=fields.Char(string="Shipping Term",compute='_compute_picking_vals')
    requested_date=fields.Date(string="Req. Ship Date")
    delivery_method_name = fields.Char(string="Ship Via",compute='_compute_picking_vals')
    # name = fields.Char(string="Name")
    # state= fields.Char(string="State")
    # carrier_id=fields.Integer(string="Carrier")
    #
    # ship_to=fields.Char(string="Ship To")
    # bill_to = fields.Char(string="Bill To")
    # requested_date=fields.Char(string="Requested Date")
    # shipping_terms=fields.Char(string="Shipping Term")
    # ship_via=fields.Char(string="Ship Via")
    # order_number=fields.Char(string="Order Number")
    # carton_information=fields.Char(string="Carton Information")
    # tracking_url=fields.Char(string="Tracking Url")
    # customer_name = fields.Char(string="Name")
    # product_id = fields.Many2one('product.template', string='Product', )
    # partner_id = fields.Many2one('res.partner', string='Customer', )
    # cost = fields.Float(string="Unit Price")
    # product_code = fields.Char(string="Product Code")
    # product_name = fields.Char(string="Name")
    # currency_id = fields.Many2one("res.currency", string="Currency",readonly=True)
    # currency_symbol=fields.Char(string="Currency Symbol")
    # item_description=fields.Char(string="Item Description")
    # qty_ordered=fields.Char(string="Qty Ordered")
    # qty_shipped = fields.Char(string="Qty Shipped")
    # qty_remaining=fields.Char(string="Qty Remainig")

    def _compute_picking_vals(self):
       for picking in self:
          if picking.sale_id:
              picking.date_deadline=picking.sale_id.date_order
              if picking.sale_id.shipping_terms:
                picking.shipping_terms=self.shipping_term(picking.sale_id.shipping_terms)
              else:
                  picking.shipping_terms = None
              if picking.sale_id.carrier_id:
                picking.delivery_method_name = picking.sale_id.carrier_id.name
              else:
                  picking.delivery_method_name = None
          else:
              picking.delivery_method_name = None
              picking.shipping_terms = None





    def shipping_term(self,i):
        switcher = {
            '1': 'Prepaid & Billed',
            '2': 'Prepaid',
            '3': 'Freight Collect'
        }
        return switcher.get(i, "")

