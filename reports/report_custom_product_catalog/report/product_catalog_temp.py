
from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.catalog_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.product'].browse(docids)}

class ReportProductWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.product_catalog_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.product'].browse(docids)}
