import logging
from odoo import api, fields, models
from datetime import datetime

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.sales_by_count.sales_by_count_template'

    @api.model
    def get_report_values(self, docids, data=None):
        records = self.env['report.sales.by.count'].browse(docids)

        old = ""
        sales = {}
        for record in records:
            product = {
                'sku_code': record.sku_code,
                'product_name': record.product_name,
                'quantity': int(float(record.quantity))}
            if old == record.location:
                sales[old]['product'].append(product)
            else:
                old = record.location
                sales[old] = {
                    'location': record.location,
                    'product': [product]}

        popup = self.env['popup.sales.by.count'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        if popup.compute_at_date:
            date = datetime.strptime(popup.start_date, '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                popup.end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'sales': sales, 'date': date}
