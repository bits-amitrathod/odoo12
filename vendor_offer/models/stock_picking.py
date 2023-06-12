
from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    arrival_date = fields.Datetime(string="Arrival Date")

    @api.model
    def create(self, vals):
        record = super(StockPicking, self).create(vals)
        for pick in self:
            purchase_order = self.env['purchase.order'].search([('name', '=', pick.origin)])
            for order in purchase_order:
                if pick.arrival_date and pick.arrival_date is not None:
                    order.arrival_date_grp = pick.arrival_date
        return record

    #@api.multi
    def write(self, vals):
        record = super(StockPicking, self).write(vals)
        if 'arrival_date' in vals:
            for pick in self:
                purchase_order = self.env['purchase.order'].search([('name', '=', pick.origin)])
                for order in purchase_order:
                    if order.arrival_date_grp and (order.arrival_date_grp != vals['arrival_date']):
                        order.arrival_date_grp = vals['arrival_date']
        return record


    #@api.multi
    def send_to_shipper(self):
        self.ensure_one()
        res = self.carrier_id.send_shipping(self)[0]
        if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
            res['exact_price'] = 0.0
        self.carrier_price = res['exact_price']
        if res['tracking_number']:
            self.carrier_tracking_ref = res['tracking_number']
        order_currency = self.sale_id.currency_id or self.company_id.currency_id
        msg = _("Shipment sent to carrier %s for shipping with tracking number %s<br/>Cost: %.2f %s") % (
            self.carrier_id.name, self.carrier_tracking_ref, self.carrier_price, order_currency.name)
        self.message_post(body=msg)


class StockInventoryActionDone(models.Model):
    _inherit = 'stock.inventory'

    def action_done(self):
        super(StockInventoryActionDone, self).action_done()
        for item in self:
            product = item.product_id.product_tmpl_id
            product._compute_quantities()
            product._compute_qty_available()