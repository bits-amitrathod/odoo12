# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class RevenueByKa(models.Model):
    _name = 'report.ka.revenue'
    _auto = False

    customer = fields.Many2one('res.partner', 'Customer Name')
    key_account = fields.Many2one('res.users', 'Key Account')
    no_of_orders = fields.Integer('No. of orders')
    total_revenue = fields.Float('Total Revenue')
    order_quota = fields.Integer(string="Order Quota", help="Number of transactions")
    revenue_quota = fields.Integer(string="Revenue Quota", help="Amount")
    progress_order_quota = fields.Char('Progress of Order Quota')
    progress_revenue_quota = fields.Char('Progress of Revenue Quota')
    currency_id = fields.Many2one('res.currency', string='Currency')
    delivery_date = fields.Datetime('Delivery Date')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """
            SELECT
                ROW_NUMBER () OVER (ORDER BY RP.id) AS id, 
                RP.id                                       AS customer, 
                RP.account_manager_cust                     AS key_account,
                COUNT(SO.partner_id)                        AS no_of_orders, 
                SUM(SOL.qty_delivered * SOL.price_reduce)   AS total_revenue, 
                RP.order_quota                              AS order_quota, 
                RP.revenue_quota                            AS revenue_quota,
                CONCAT(ROUND((COUNT(SO.partner_id)/RP.order_quota::float)*100), '%') AS progress_order_quota,
                CONCAT(ROUND((SUM(SOL.qty_delivered * SOL.price_reduce)/RP.revenue_quota::float)*100), '%') AS progress_revenue_quota,
                SOL.currency_id     AS currency_id,
                date_trunc('month', SP.date_done)   AS delivery_date
                
                FROM public.res_partner RP
                
                INNER JOIN 
                    public.sale_order SO 
                ON 
                    RP.id = SO.partner_id
                INNER JOIN 
                    (SELECT DISTINCT ON (order_id) order_id, qty_delivered, price_reduce, currency_id FROM sale_order_line) AS SOL
                ON 
                    SO.id = SOL.order_id
                INNER JOIN 
                    (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin) AS SP 
                ON 
                    SO.id = SP.sale_id 
                        
                WHERE SO.state NOT IN ('cancel', 'void') AND RP.account_manager_cust IS NOT NULL
                             

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
            select_query = select_query + "AND RP.account_manager_cust = '" + str(key_account_id) + "'"

        group_by = """
                    GROUP BY
                        RP.id, date_trunc('month', SP.date_done), SOL.currency_id
                        """

        sql_query = select_query + group_by

        self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code
class RevenueByKaExport(models.TransientModel):
    _name = 'report.ka.revenue.export'

    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range ')
    ], string="Compute", default=0, help="Choose Show All or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)),
                             help="Choose a date to get the Revenu By Key Account at that  Start date")
    end_date = fields.Date('End Date',default=fields.date.today(), help="Choose a date to get the Revenue By Key Account at that  End date")
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
