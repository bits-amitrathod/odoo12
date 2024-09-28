from odoo import api, fields, models,_
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc


class SaleQuotationExport(models.TransientModel):
    _name = 'sale.quotation.history'
    _description = "Sale Quotation Export"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products")
    order_partner_id = fields.Many2one('res.partner', string='Customer')
    contract_id = fields.Many2one('contract.contract', string='Contract')
    order_account_manager_cust = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True)"
                                                                                               ",('share','=',False)]")

    #@api.multi
    def open_table(self):
        tree_view_id = self.env.ref('sales_quotation_history.sale_quotation_export_list_view').id
        form_view_id = self.env.ref('sales_quotation_history.view_sales_quotation_export_cstm').id
        if self.start_date and self.end_date:
            e_date = SaleQuotationExport.string_to_date(str(self.end_date))
            e_date = e_date + datetime.timedelta(days=1)
            s_date = SaleQuotationExport.string_to_date(str(self.start_date))
            sale_order_line = self.env['sale.order.line'].search([('create_date', '>=', str(s_date)), ('create_date', '<=', str(e_date)),('state', 'in', ('draft','draft')),]).ids
        else:
            sale_order_line = self.env['sale.order.line'].search([('state', 'in', ('draft', 'draft')), ]).ids
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Sales Quotation History'),
            'res_model': 'sale.order.line',
            'domain': [('id', 'in', sale_order_line),('price_unit','>=',0),('product_uom_qty','>',0)],
            'target': 'main'
        }

        if self.product_id and self.order_partner_id:
            action['domain'].append(('product_id', 'in', self.product_id.ids))
            action['domain'].append(('order_partner_id', '=', self.order_partner_id.id))
        elif self.product_id:
            action['domain'].append(('product_id', 'in', self.product_id.ids))
        elif self.order_partner_id:
            action['domain'].append(('order_partner_id', '=', self.order_partner_id.id))
        if self.contract_id:
            action['domain'].append(('order_partner_id.contract', '=', self.contract_id.id))
        if self.order_account_manager_cust:
            action['domain'].append(('order_partner_id.account_manager_cust', '=', self.order_account_manager_cust.id))
        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
