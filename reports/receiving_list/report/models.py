from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.receiving_list.receiving_list_temp'
    _description = "ReportSalesSalespersonWise"

    def _get_report_values(self, docids, data=None):

        if data:
            if data['order_type'] == '1':
                records = self._get_purchase_order_data(data['order_id'])
            else:
                records = self._get_sale_order_data(data['order_id'])
            return {
                'data': records,
                'order_type': data['order_type']
            }
        else:
            records =self._receipts(docids)
            return {
                'data': records,
                'order_type': 'PO'
            }

    def _get_purchase_order_data(self, purchase_order):
        records = self.env['report.receiving.list.po'].search([('order_id', '=', purchase_order)])
        return records

    def _get_sale_order_data(self, sales_order):
        records = self.env['report.receiving.list.so'].search([('order_id', '=', sales_order)])
        return records

    def _receipts(self,docids):
        self.env['report.receiving.list.po'].delete_and_create()
        sp= self.env['stock.picking'].search([('id', '=', docids[0])])
        po = self.env['purchase.order'].search([('name', '=', sp[0].origin)])
        records = self._get_purchase_order_data(po[0].id)
        return records