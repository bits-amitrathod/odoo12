
from odoo import api, fields, models



class ReportProducts(models.AbstractModel):
    _name = 'report.tps_report_sale.report_products'
    _description = "Report Total Products Sale"

    @api.model
    def _get_report_values(self, docids, data=None):
        view='total_product_sale'
        popup = self.env['tps.popup.view'].search([('create_uid', '=', self._uid)], limit=1,
                                                                 order="id desc")


        records = self.env['total_product_sale'].browse(docids)
        return {
            'data': records,'popup':popup}




    # @api.model
    # def get_report_values(self, docids, data=None):
    #     purchase_orders = self.env['sale.order'].browse(docids)
    #     return {
    #         'doc_ids': data.get('ids'),
    #         'doc_model': data.get('model'),
    #         'data': purchase_orders,
    #     }



