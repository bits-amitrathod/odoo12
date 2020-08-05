# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class RevenueByKa(models.Model):
    _name = 'report.ka.revenue'
    _auto = False

    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    # date_order = fields.Datetime('Order Date')
    delivery_date = fields.Datetime('Delivery Date')
    key_account = fields.Many2one('res.users', 'Key Account')
    customer = fields.Many2one('res.partner', 'Customer Name')
    # salesperson = fields.Many2one('res.users', 'Salesperson')
    # product_tmpl_id = fields.Many2one('product.template', "Product")
    # qty_done = fields.Integer('Quantity')
    # unit_price = fields.Float('Unit Price')
    total_amount = fields.Float('Total')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        #  For salesperson              SO.user_id                          AS salesperson,

        select_query = """
            SELECT
                ROW_NUMBER () OVER (ORDER BY SO.id) AS id,
                SO.id                               AS sale_order_id,
                SO.partner_id                       AS customer,
                SO.date_order                       AS date_order,
                SO.account_manager                  AS key_account,
                SO.state                            AS status,  
                SP.date_done                        AS delivery_date,
                SUM(SOL.qty_delivered * SOL.price_reduce)  AS total_amount 
            FROM public.sale_order SO
                INNER JOIN 
                    public.sale_order_line SOL 
                ON 
                    SO.id = SOL.order_id
                INNER JOIN 
                    public.stock_picking SP 
                ON 
                    SO.id = SP.sale_id
                
                WHERE SO.state NOT IN ('cancel', 'void') AND SO.account_manager IS NOT NULL AND SP.state = 'done' AND SP.picking_type_id = 5

        """

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        compute_at = self.env.context.get('compute_at')
        key_account_id = self.env.context.get('key_account')

        if compute_at:
            if start_date and start_date is not None and end_date and end_date is not None:
                select_query = select_query + " AND SP.date_done BETWEEN '" + str(
                    start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"
        if key_account_id:
            select_query = select_query + "AND SO.account_manager = '" + str(key_account_id) + "'"

        group_by = """
                    GROUP BY
                     SO.id, SP.date_done                
                        """

        sql_query = select_query + group_by

        self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()



#Export code

class RevenueByKaExport(models.TransientModel):
    _name = 'report.ka.revenue.export'

    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose Show All or from a specific date in the past.")

    start_date = fields.Date('Start Date',
                             help="Choose a date to get the Revenu By Key Account at that  Start date",
                             default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Revenue By Key Account at that  End date",
                           default=fields.date.today())
    key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
                                                                            "('share','=',False)]")

    def download_excel_ka_revenue(self):

        if self.compute_at_date:
            e_date = self.string_to_date(str(self.end_date))
            e_date = e_date + datetime.timedelta(days=1)
            s_date = self.string_to_date(str(self.start_date))
            if self.key_account and self.key_account is not None:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_ka_export/' + str(s_date) + '/' + str(e_date) + '/' +
                           str(self.key_account.id),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_ka_export/' + str(s_date) + '/' + str(e_date) + '/' + str('none'),
                    'target': 'new'
                }
        else:
            if self.key_account:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_ka_export/' + str('all') + '/' + str('all') + '/' +
                           str(self.key_account.id),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_ka_export/' + str('all') + '/' + str('all') + '/' + str(
                        'none'),
                    'target': 'new'
                }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

    # Uncomment for original Query

    # select_query = """
    #             SELECT
    #                 ROW_NUMBER () OVER (ORDER BY SP.id) AS id,
    #                 SO.id                               AS sale_order_id,
    #                 SO.partner_id                       AS customer,
    #                 SP.date_done                        AS delivery_date,
    #                 SO.account_manager                  AS key_account,
    #                 PT.id                               AS product_tmpl_id,
    #                 SOL.price_unit                      AS unit_price,
    #                 SUM(SML.qty_done)                   AS qty_done,
    #                 SUM(SML.qty_done) * SOL.price_unit  AS total_amount
    #             FROM
    #                 public.stock_picking SP
    #
    #             INNER JOIN
    #                 public.sale_order SO
    #             ON
    #                 (
    #                     SP.sale_id = SO.id)
    #             INNER JOIN
    #                 public.sale_order_line SOL
    #             ON
    #                 (
    #                     SO.id = SOL.order_id)
    #             INNER JOIN
    #                 public.res_users RU
    #             ON
    #                 (
    #                     SO.account_manager = RU.id)
    #             INNER JOIN
    #                 public.res_partner RP
    #             ON
    #                 (
    #                     RU.partner_id = RP.id)
    #             INNER JOIN
    #                 public.stock_move SM
    #             ON
    #                 (
    #                     SP.id = SM.picking_id)
    #             INNER JOIN
    #                 public.stock_move_line SML
    #             ON
    #                 (
    #                     SM.id = SML.move_id)
    #             INNER JOIN
    #                 public.stock_production_lot SPL
    #             ON
    #                 (
    #                     SML.lot_id = SPL.id)
    #             INNER JOIN
    #                 public.product_product PP
    #             ON
    #                 (
    #                     SM.product_id = PP.id)
    #             INNER JOIN
    #                 public.product_template PT
    #             ON
    #                 (
    #                     PP.product_tmpl_id = PT.id)
    #
    #             WHERE SO.state NOT IN ('cancel', 'void') AND SP.state = 'done' AND SP.picking_type_id = 5
    #                 AND SM.product_id = SOL.product_id AND SO.account_manager IS NOT NULL
    #
    #         """

    # Uncomment for original Query

    # group_by = """
    #                        GROUP BY
    #                            SP.id, SO.id, SO.account_manager,PT.id, SOL.price_unit
    #                                """
