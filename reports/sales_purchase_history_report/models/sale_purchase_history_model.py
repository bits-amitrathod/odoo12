# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class SalePurchaseHistory(models.Model):
    _inherit = "sale.order.line"

    # product_name = fields.Char("Product Name", compute='_compare_data',store=False)
    product_sku_ref = fields.Char("Product SKU", compute='_compare_data', store=False)
    customer_name = fields.Char("Customer Name",compute='_compare_data', store=False)
    delivered_date = fields.Datetime("Delivered Date",compute='_compare_data', store=False)
    qty_delivered_converted = fields.Float("Delivered Qty",compute='_compare_data', store=False,digits='Product Unit of Measure')
    unit_price_converted = fields.Monetary("Unit Price", currency_field='currency_id', store=False)
    total_price_converted = fields.Monetary("Total", currency_field='currency_id', store=False)
    product_uom_converted = fields.Many2one('uom.uom', 'Unit of Measure', currency_field='currency_id', store=False)
    account_manager_cust_name = fields.Char(string="Key Account", compute='_compare_data', store=False)
    sales_person_cust_name = fields.Char(string="Business Development", compute='_compare_data', store=False)
    is_broker_opt = fields.Boolean(string="Is Broker", compute='_compare_data', store=False)
    is_shared_opt = fields.Boolean(string="Is Shared", compute='_compare_data', store=False)
    sales_person_cust_name = fields.Char(string="Business Development", compute='_compare_data', store=False)
    sales_team_id = fields.Char(string="Sales Team", compute='_compare_data', store=False)
    sale_sales_margine = fields.Char(string="Sales Level", compute='_compare_data', store=False)
    quotations_per_code = fields.Integer(string='Open Quotations Per Code',
                                         compute='_compare_data',
                                         readonly=True, store=False)
    # user_id = fields.Many2one('res.users', string='User', store=False)
    # currency_id = fields.Many2one("res.currency", string="Currency",readonly=True)
    # product_uom = fields.Char(string='UOM', store=False)

    #@api.multi
    def _compare_data(self):
        for sale_order_line in self:
            sale_order_line.customer_name = sale_order_line.order_id.partner_id.name
            sale_order_line.account_manager_cust_name = sale_order_line.order_id.partner_id.account_manager_cust.name
            sale_order_line.sales_person_cust_name = sale_order_line.order_id.partner_id.user_id.name
            sale_order_line.is_broker_opt = sale_order_line.order_id.partner_id.is_broker
            sale_order_line.is_shared_opt = sale_order_line.order_id.is_share
            sale_order_line.sales_team_id = sale_order_line.order_id.team_id.name
            sale_order_line.sale_sales_margine = sale_order_line.order_id.partner_id.sale_margine
            sale_order_line.qty_delivered_converted = None 
            sale_order_line.product_sku_ref = sale_order_line.product_id.product_tmpl_id.sku_code
            sale_order_line_list = self.env['sale.order.line'].search([('product_id', '=', sale_order_line.product_id.id), ('state', 'in', ('draft', 'sent'))])
            sale_order_line.quotations_per_code = len(sale_order_line_list)
            if sale_order_line.order_id.state != 'cancel':
                stock_location=self.env['stock.location'].search([('name', '=', 'Customers')])
                if stock_location:
                    stock_picking = self.env['stock.picking'].search([('sale_id', '=', sale_order_line.order_id.id),('state', '=', 'done'),('location_dest_id','=',stock_location.id)])
                    if stock_picking:
                        for picking in stock_picking:
                            for move_line in picking.move_line_ids:
                                if move_line.product_id.id == sale_order_line.product_id.id:
                                    #sale_order_line.qty_delivered_converted += move_line.product_uom_qty
                                    sale_order_line.qty_delivered_converted = sale_order_line.qty_delivered

                                    discount_val = sale_order_line.discount
                                    if discount_val and (discount_val > 0):
                                        sale_order_line.unit_price_converted = (sale_order_line.price_unit)-(sale_order_line.price_unit * discount_val/100)
                                        sale_order_line.total_price_converted = ( (
                                                sale_order_line.price_unit * sale_order_line.qty_delivered))-((
                                                    sale_order_line.price_unit * sale_order_line.qty_delivered) * discount_val/100)
                                    else:
                                        sale_order_line.unit_price_converted = sale_order_line.price_unit
                                        sale_order_line.total_price_converted = (
                                                sale_order_line.price_unit * sale_order_line.qty_delivered)
                                    sale_order_line.product_uom_converted = move_line.product_uom_id
                            if picking.date_done:
                                sale_order_line.delivered_date = picking.date_done
                            else:
                                sale_order_line.delivered_date = None
                    else:
                        sale_order_line.delivered_date = None


class SalePurchaseHistoryExport(models.TransientModel):
    _name = 'salepuchasehistory.export'
    _description = 'salepuchasehistory export'

    compute_at_date = fields.Selection([
        ('0', 'Show All'),
        ('1', 'Date Range ')
    ], string="Compute", default='0', help="Choose Show All or from a specific date in the past.")

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def download_excel_sale_puchase_history(self):

        if self.compute_at_date:
            e_date = self.string_to_date(str(self.end_date))
            e_date = e_date + datetime.timedelta(days=1)
            s_date = self.string_to_date(str(self.start_date))

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/sale_purchase_history_export/'+str(s_date)+'/'+str(e_date),
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/sale_purchase_history_export/'+str('all')+'/'+str('all'),
                'target': 'new'
            }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
