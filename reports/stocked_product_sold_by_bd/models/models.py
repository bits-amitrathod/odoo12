# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class StockedProductSoldByBd(models.Model):
    _name = 'report.product.sold.by.bd'
    _description = 'Short date and over stocked product sold by BD'
    _auto = False

    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    customer_id = fields.Many2one('res.partner', 'Customer Name')
    status = fields.Char('Status')
    date_order = fields.Datetime('Order Date')
    delivery_date = fields.Datetime('Delivery Date')
    sku_code = fields.Char('Product SKU')
    #key_account = fields.Many2one('res.users', 'Key Account')
    business_development = fields.Many2one('res.users', 'Business Development')
    product_tmpl_id = fields.Many2one('product.template', "Product")
    product_uom_id = fields.Many2one('uom.uom', 'Product UOM')
    qty_done = fields.Integer('Delivered Quantity')
    unit_price = fields.Float('Unit Price')
    total_amount = fields.Float('Total')
    currency_id = fields.Many2one('res.currency', string='Currency')

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """
            SELECT
                ROW_NUMBER () OVER (ORDER BY SP.id) AS id, 
                SO.id               AS sale_order_id, 
                SO.partner_id       AS customer_id, 
                SO.date_order       AS date_order, 
                SP.date_done        AS delivery_date,
                SO.user_id          AS business_development, 
                SO.state            AS status, 
                PT.id               AS product_tmpl_id, 
                PT.uom_id           AS product_uom_id, 
                PT.sku_code         AS sku_code, 
                SOL.price_reduce    AS unit_price, 
                SOL.currency_id     AS currency_id,

                CASE WHEN (SELECT SUM(SMLS.qty_done)
                FROM public.stock_picking SPS
                INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                INNER JOIN public.stock_production_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7) is null THEN SUM(SML.qty_done) ELSE
                (SUM(SML.qty_done) - (SELECT SUM(SMLS.qty_done)
                FROM public.stock_picking SPS
                INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                INNER JOIN public.stock_production_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7)) END AS qty_done,


                CASE WHEN (SELECT SUM(SMLS.qty_done)
                FROM public.stock_picking SPS
                INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                INNER JOIN public.stock_production_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7) is null THEN SUM(SML.qty_done) ELSE
                (SUM(SML.qty_done) - (SELECT SUM(SMLS.qty_done)
                FROM public.stock_picking SPS
                INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                INNER JOIN public.stock_production_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7)) END * SOL.price_reduce AS total_amount

            FROM 
                public.sale_order SO

            INNER JOIN 
                public.sale_order_line SOL 
            ON 
                (
                    SO.id = SOL.order_id)
            INNER JOIN 
                public.stock_picking SP 
            ON 
                (
                    SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5)
            INNER JOIN 
                public.stock_move SM 
            ON 
                (
                    SP.id = SM.picking_id AND SM.product_id = SOL.product_id)
            INNER JOIN 
                public.stock_move_line SML
            ON 
                (
                    SM.id = SML.move_id)
            INNER JOIN 
                public.stock_production_lot SPL 
            ON 
                (
                    SML.lot_id = SPL.id AND SPL.use_date <= SP.date_done + INTERVAL '6 MONTH')
            INNER JOIN 
                public.product_product PP 
            ON 
                (
                    SM.product_id = PP.id)
            INNER JOIN 
                public.product_template PT 
            ON 
                (
                    PP.product_tmpl_id = PT.id)

            WHERE SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL AND SO.account_manager IS NULL

        """

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        compute_at = self.env.context.get('compute_at')
        #key_account_id = self.env.context.get('key_account')
        business_development_id = self.env.context.get('business_development')

        if compute_at == '1':
            if start_date and start_date is not None and end_date and end_date is not None:
                select_query = select_query + " AND SP.date_done BETWEEN '" + str(
                    start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"
        if business_development_id:
            select_query = select_query + "AND SO.user_id = '" + str(business_development_id) + "'"

        group_by = """
                    GROUP BY

                        SM.product_id, SO.id, SP.date_done, PT.id, SOL.price_reduce, SOL.currency_id, SP.id

                        """

        sql_query = select_query + group_by

        self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


class StockedProductSoldByBdExport(models.TransientModel):
    _name = 'report.product.sold.by.bd.export'
    _description = 'Short date and over stocked product sold by BD export'

    compute_at_date = fields.Selection([
        ('0', 'Show All'),
        ('1', 'Date Range ')
    ], string="Compute", default='0', help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date(string="Start Date", default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date(string="End Date", default=fields.date.today())
    # key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
    #                                                                         "('share','=',False)]")
    business_development = fields.Many2one('res.users', 'Business Development', domain="[('active', '=', True)]")

    def download_excel_product_sold_by_bd(self):

        if self.compute_at_date == '1':
            e_date = self.string_to_date(str(self.end_date))
            e_date = e_date + datetime.timedelta(days=1)
            s_date = self.string_to_date(str(self.start_date))
            if self.business_development and self.business_development is not None:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/product_sold_by_bd_export/' + str(s_date) + '/' + str(e_date) + '/' +
                           str(self.business_development.id),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/product_sold_by_bd_export/' + str(s_date) + '/' + str(e_date) + '/' + str(
                        'none'),
                    'target': 'new'
                }
        else:
            if self.business_development:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/product_sold_by_bd_export/' + str('all') + '/' + str('all') + '/' +
                           str(self.business_development.id),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/product_sold_by_bd_export/' + str('all') + '/' + str('all') + '/' + str('none'),
                    'target': 'new'
                }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()