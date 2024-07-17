
from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_price_list.price_list_temp'
    _description = "Report Sales Salesperson Wise"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {'data': self.env['product.product'].browse(docids)}


class CustProductPriceList(models.AbstractModel):
    _name = 'report.report_price_list.cust_price_list_temp'
    _description = "Cust Product PriceList"

    @api.model
    def _get_report_values(self, docids, data=None):
        popup = self.env['inventory.customer_price_list_popup'].search([('create_uid', '=', self._uid)], limit=1,order="id desc")
        return {'data': self.env['inv.customer_price_list'].browse(docids),'customer_name':popup.customer_list.display_name}