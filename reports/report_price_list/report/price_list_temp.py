
from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_price_list.price_list_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.template'].browse(docids)}


class CustProductPriceList(models.AbstractModel):
    _name = 'report.report_price_list.cust_price_list_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.template'].browse(docids)}