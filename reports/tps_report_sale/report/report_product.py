
from odoo import api, fields, models



class ReportProducts(models.AbstractModel):
    _name = 'report.tps_report_sale.report_products'

    @api.model
    def get_report_values(self, docids, data=None):
        if len(docids) == 1:
            ids = "(" + str(docids[0]) + ")"
        else:
            ids = str(tuple(docids))
        view='total_product_sale'
        records = "select tps.sku_code,tps.product_name,concat(tps.currency_symbol,' ',cast(tps.total_sales as varchar)) as total_sales,tps.start_date,tps.end_date  from  " + view +" as tps where id in "  + ids
        self._cr.execute(records)
        records = self._cr.fetchall()
        for record in records:
            record
        return {
            'data': records}




    # @api.model
    # def get_report_values(self, docids, data=None):
    #     purchase_orders = self.env['sale.order'].browse(docids)
    #     return {
    #         'doc_ids': data.get('ids'),
    #         'doc_model': data.get('model'),
    #         'data': purchase_orders,
    #     }



