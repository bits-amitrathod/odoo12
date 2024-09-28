
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class SalesQuotationExport(models.Model):
    _inherit = "sale.order.line"

    qe_product_sku_ref = fields.Char("Product SKU", compute='_compare_data_exp', store=False)
    qe_customer_name = fields.Char("Customer Name", compute='_compare_data_exp', store=False)
    qe_delivered_date = fields.Datetime("Delivered Date", compute='_compare_data_exp', store=False)
    qe_qty_delivered_converted = fields.Float("Delivered Qty", compute='_compare_data_exp', store=False,
                                           digits='Product Unit of Measure')
    qe_unit_price_converted = fields.Monetary("Unit Price", currency_field='currency_id', store=False)
    qe_total_price_converted = fields.Monetary("Total", currency_field='currency_id', store=False)
    qe_product_uom_converted = fields.Many2one('uom.uom', 'Unit of Measure', currency_field='currency_id', store=False)
    qe_account_manager_cust_name = fields.Char(string="Key Account", compute='_compare_data_exp', store=False)
    qe_quotations_per_code = fields.Integer(string='Open Quotations Per Code',
                                         compute='_compare_data_exp',
                                         readonly=True, store=False)

    def _valid_field_parameter(self, field, name):
        return name == 'currency_field' or super()._valid_field_parameter(field, name)

    #@api.multi
    def _compare_data_exp(self):
        for sale_order_line in self:
            sale_order_line.qe_customer_name = sale_order_line.order_id.partner_id.name
            sale_order_line_list_qe = self.env['sale.order.line'].search(
                [('product_id', '=', sale_order_line.product_id.id), ('state', 'in', ('draft', 'sent'))])
            sale_order_line.qe_quotations_per_code = len(sale_order_line_list_qe)
            sale_order_line.qe_account_manager_cust_name = sale_order_line.order_id.partner_id.account_manager_cust.name
            sale_order_line.qe_product_sku_ref = sale_order_line.product_id.product_tmpl_id.sku_code
            sale_order_line.qe_unit_price_converted = sale_order_line.price_unit
            sale_order_line.qe_total_price_converted += (
                    sale_order_line.price_unit * sale_order_line.product_uom_qty)
            sale_order_line.qe_product_uom_converted = sale_order_line.product_uom


class SaleQuotationExportFile(models.TransientModel):
    _name = 'salequotationexport.export'
    _description = 'salequotationexport export'

    def download_excel_sale_quotation_export(self):

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/export/sale_quotation_export_xl',
            'target': 'new'
        }
