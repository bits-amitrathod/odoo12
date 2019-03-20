from odoo import api, models


class ReportSalesOrderInvoices(models.AbstractModel):
    _name = 'report.report_sales_order_invoices.sales_order_invoices'

    @api.model
    def get_report_values(self, docids, data=None):
        invoices = self.env['account.invoice'].search([('id','in',docids)])
        orders = {}
        for invoice in invoices:
            orders[invoice.id] = self.env['sale.order'].search([('name','=',invoice.origin)])
        return {
            'invoices': invoices,
            'orders': orders,
            'hasattr':hasattr
        }
