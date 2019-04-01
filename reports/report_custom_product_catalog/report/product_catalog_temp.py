
from odoo import api, models

from reports.report_custom_product_catalog.models.catalog import InventoryCustomProductPopUp


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.catalog_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        popup = self.env['popup.custom.product.catalog'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        context = {}
        if popup.start_date or popup.end_date:
            product_list = InventoryCustomProductPopUp.fetchData(popup)
            context = {'production_lot_ids': product_list[0][1]}
        return {'data': self.env['product.product'].with_context(context).browse(docids)}

class ReportProductWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.product_catalog_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.product'].browse(docids)}
