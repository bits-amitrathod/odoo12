
from odoo import models, fields, api, _


class StockMoveOfferPrice(models.Model):
    _description = "Stock Move Offer Price"
    _inherit = "stock.move"
    _order = 'product_id asc'

    re_product_offer_price = fields.Monetary(string="Offer Price", compute='_set_offer_price_re')
    re_total_product_retail = fields.Monetary(string="Total Retail Price", compute='_set_offer_price_re')
    currency_id = fields.Many2one('res.currency', string='Currency', store=False)
    re_vendor_offer_data = fields.Boolean(compute='_set_offer_price_re')
    re_expiration_date_str = fields.Char(string="Expected Expiration Date",compute='_set_offer_price_re')

    def _set_offer_price_re(self):
        for line in self:
            line.currency_id = line.product_id.currency_id.id
            po_num = line.origin
            if po_num:
                po_order = self.env['purchase.order'].search(
                    [('name', '=', po_num),('state', '=', 'purchase')])
                line.re_vendor_offer_data = po_order.vendor_offer_data
                po_prods =[]
                if po_order.id:
                    po_line_id = line.purchase_line_id.id
                    po_prods = self.env['purchase.order.line'].search(
                        [('product_id', '=', line.product_id.id),('order_id', '=', po_order.id),
                         ('id', '=', po_line_id)])
                if po_prods != []:
                    for obj in po_prods:
                        line.update({
                            're_product_offer_price': obj.price_unit,
                            're_total_product_retail': obj.product_retail,
                            're_expiration_date_str': obj.expiration_date_str
                        })
                else:
                    line.re_expiration_date_str = None
                    line.re_total_product_retail = None
                    line.re_product_offer_price = None

            else:
                line.re_expiration_date_str = None
                line.re_total_product_retail = None
                line.re_product_offer_price = None
                line.re_vendor_offer_data = None

