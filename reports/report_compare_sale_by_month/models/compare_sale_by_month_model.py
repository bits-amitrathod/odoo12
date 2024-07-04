
from odoo import api, fields, models
import datetime
import odoo.addons.decimal_precision as dp

class CompareSaleByMonth(models.Model):
    _inherit = "product.product"

    # sku_name = fields.Char("Product ",store=False)
    product_name = fields.Char("Product Name ",compute = '_compare_data',)
    last_month_total_qty = fields.Float("Last Month Total Qty", compute = '_compare_data', store=False,digits='Product Unit of Measure')
    last_month_total_amount = fields.Monetary("Last Month Total Amount", compute = '_compare_data',)
    current_month_total_qty = fields.Float("Current Month Total Qty", compute = '_compare_data',digits='Product Unit of Measure')
    current_month_total_amount = fields.Monetary("Current Month Total Amount", compute = '_compare_data',)
    # location = fields.Char(string='Location')

    def _compare_data(self):
        dat=self.env.context.get('dat')
        if dat and not dat is None:
            self.fetch_data(dat)

    def fetch_data(self,dat):
        for order in self:
            value = str(order.id) in dat
            if value:
                object = dat[str(order.id)]
                if int(object['current_month_total_qty']) > 0 or int(object['last_month_total_qty']) > 0:
                    # order.sku_name = dat[order.id].sku
                    order.product_name = object['product_name']
                    order.last_month_total_qty = object['last_month_total_qty']
                    order.last_month_total_amount = object['last_month_total_amount']
                    order.current_month_total_qty = object['current_month_total_qty']
                    order.current_month_total_amount = object['current_month_total_amount']
