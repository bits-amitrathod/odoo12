from odoo import models, fields, api, _


class VendorOfferProductLineNew(models.Model):
    _inherit = "purchase.order.line"
    _description = "Vendor Offer Product line New"

    # New for Appraisal
    multiplier_app_new = fields.Many2one('multiplier.multiplier', string="Multiplier")
    product_qty_app_new = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)

    def compute_total_line_vendor(self):
        for line in self:

            taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                               line.product_qty, product=line.product_id,
                                               partner=line.order_id.partner_id)

            taxes = line.taxes_id.compute_all(float(line.product_offer_price), line.order_id.currency_id,
                                              line.product_qty, product=line.product_id,
                                              partner=line.order_id.partner_id)

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_subtotal': taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_unit': line.product_offer_price,

                'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                'product_retail': taxes1['total_excluded'],
                'rt_price_total': taxes1['total_included'],
            })



