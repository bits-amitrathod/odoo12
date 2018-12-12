import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_month.sales_by_month_template'

    @api.model
    def get_report_values(self, docids, data=None):
        records = self.env['product.product'].browse(docids)

        data = []
        for product in records:
            record = {'product_name': product.product_tmpl_id.name,
                      'sku_name': product.product_tmpl_id.sku_code}

            sale_order_lines = self.env['sale.order.line'].search([('product_id', '=', product.id)])
            for sale_order_line in sale_order_lines:
                record['total_sale_qty'] = product.total_sale_qty + sale_order_line.product_uom_qty
                if 'product_price' in record:
                    record['product_price'] = record['product_price'] + sale_order_line.price_total
                else:
                    record['product_price'] = sale_order_line.price_total
            data.append(record)
        return {
            'data': records.sorted(key=lambda r: r.total_sale_qty, reverse=True)}
