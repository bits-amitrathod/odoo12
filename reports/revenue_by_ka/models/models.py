# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
import calendar
import math
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging
import odoo.addons.decimal_precision as dp
from dateutil import relativedelta

_logger = logging.getLogger(__name__)


class RevenueByKa(models.Model):
    _name = 'report.ka.revenue'
    _description = "Revenue By Ka"

    _auto = False
    _order = "customer"

    customer = fields.Many2one('res.partner', 'Customer Name')
    key_account = fields.Many2one('res.users', 'Key Account')
    no_of_orders = fields.Integer('No. of orders')
    total_revenue = fields.Float('Total Revenue')
    order_quota = fields.Float(string="Order Quota", help="Number of transactions", digits='Product Price')
    revenue_quota = fields.Integer(string="Revenue Quota", help="Amount")
    progress_order_quota = fields.Float('Progress of Order Quota %', digits='Product Price')
    progress_revenue_quota = fields.Float('Progress of Revenue Quota %', digits='Product Price')
    currency_id = fields.Many2one('res.currency', string='Currency')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=False):
        fields = ['currency_id', 'customer', 'key_account', 'no_of_orders', 'order_quota', 'progress_order_quota', 'total_revenue', 'revenue_quota', 'progress_revenue_quota']
        res = super(RevenueByKa, self).read_group(domain, fields, groupby, offset, limit=limit, orderby=orderby, lazy=lazy)
        for line in res:
            if 'order_quota' in line and line['order_quota'] and 'revenue_quota' in line and line['revenue_quota']:
                if line['order_quota'] > 0:
                    if 'key_account' in groupby and 'customer' not in line:
                        line['order_quota'] = math.ceil(line['order_quota'])
                        line['progress_order_quota'] = (line['no_of_orders']/line['order_quota'])*100
                    else:
                        line['progress_order_quota'] = (line['no_of_orders'] / line['order_quota']) * 100
                if line['revenue_quota'] > 0:
                    line['progress_revenue_quota'] = (line['total_revenue'] / line['revenue_quota'])*100
        return res

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date_month = self.env.context.get('start_date')
        end_date_month = self.env.context.get('end_date')
        key_account_id = self.env.context.get('key_account')
        date_difference = self.env.context.get('date_difference')

        if start_date_month and end_date_month:
            select_query = """
                SELECT 
                    ROW_NUMBER () OVER (ORDER BY RP.id)         AS id, 
                    RP.id                                       AS customer, 
                    RP.account_manager_cust                     AS key_account,
                    CASE WHEN SOL.currency_id is NULL THEN 3 ELSE SOL.currency_id END AS currency_id,
                    CASE WHEN COUNT(SO.no_of_order) > 0 THEN COUNT(SO.no_of_order) ELSE 0 END AS no_of_orders,
                    CASE WHEN SUM(SOL.revenue) > 0 THEN SUM(SOL.revenue) ELSE 0 END AS total_revenue,
                    
                    """
            select_query = select_query + " CASE WHEN RP.order_quota > 0 THEN RP.order_quota*" + \
                           str(date_difference) + " ELSE 0 END AS order_quota, " + \
                           " CASE WHEN RP.order_quota > 0 THEN (COUNT(SO.no_of_order)/(RP.order_quota*" + \
                            str(date_difference) + "))*100 ELSE 0 END AS progress_order_quota," + \
                            " CASE WHEN RP.revenue_quota > 0 THEN RP.revenue_quota *" + str(date_difference) + \
                           " ELSE 0 END AS revenue_quota," + \
                            " CASE WHEN RP.revenue_quota > 0 THEN SUM(SOL.revenue)/(RP.revenue_quota*" + str(date_difference) + \
                            ")*100 ELSE 0 END AS progress_revenue_quota"

            select_query = select_query + """
                
                FROM public.res_partner RP
                
                LEFT JOIN 
                    (SELECT id, COUNT(sale_order.id) AS no_of_order, sale_order.partner_id, sale_order.create_date 
                        FROM public.sale_order sale_order
                    LEFT JOIN (SELECT DISTINCT ON (origin) origin, date_done, sale_id 
                        FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin) AS SP 
                    ON sale_order.id = SP.sale_id
                    WHERE state not in ('cancel', 'void') AND """

            select_query = select_query + "SP.date_done >= '" + str(start_date_month) + "' AND SP.date_done <= '" + \
                                                                                    str(end_date_month) + "'"

            select_query = select_query + """   GROUP BY id, partner_id) AS SO ON RP.id = SO.partner_id
    
                LEFT JOIN 
                    (SELECT DISTINCT ON (order_id) order_id, SUM(qty_delivered * price_reduce) AS revenue, currency_id 
                        FROM sale_order_line
                        GROUP BY order_id, currency_id) AS SOL ON SO.id = SOL.order_id
                
                WHERE RP.account_manager_cust IS NOT NULL          
                                 
            """

            if key_account_id:
                select_query = select_query + "AND RP.account_manager_cust = '" + str(key_account_id) + "'"

            group_by = """
                        GROUP BY
                            RP.id, SO.no_of_order, SOL.currency_id
                            
                            ORDER BY RP.name
                            """

            sql_query = select_query + group_by

            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")
        else:
            # This Code For only console error resolve purposr
            self.env.cr.execute('''
                         CREATE OR REPLACE VIEW %s AS (
                         SELECT  so.id AS id,
                                 so.name AS name
                         FROM sale_order so
                         )''' % (self._table)
                                )

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code
class RevenueByKaExport(models.TransientModel):
    _name = 'report.ka.revenue.export'
    _description = "Revenue By Ka Export"

    start_month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                    ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
                                    ('09', 'September'),
                                    ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Start Month',
                                   required=True)

    start_year = fields.Selection([(str(num), str(num)) for num in range(2010, (datetime.datetime.now().year) + 20)],
                                  'Start Year', default=str(datetime.datetime.now().year), required=True)

    end_month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                  ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                  ('10', 'October'), ('11', 'November'), ('12', 'December')], 'End Month',
                                 required=True)

    end_year = fields.Selection([(str(num), str(num)) for num in range(2010, (datetime.datetime.now().year) + 20)],
                                'End Year', default=str(datetime.datetime.now().year), required=True)

    key_account = fields.Many2one('res.users', string="Key Account", domain="[('active', '=', True), "
                                                                            "('share','=',False)]")

    def download_excel_ka_revenue(self):

        start_date = datetime.datetime.strptime(str(self.start_year) + "-" + str(self.start_month) + "-01",
                                                "%Y-%m-%d").date()

        end_date_custom = datetime.datetime.strptime(str(self.end_year) + "-" + str(self.end_month) + "-15", "%Y-%m-%d")

        end_date = datetime.datetime(end_date_custom.year, end_date_custom.month,
                                     calendar.mdays[end_date_custom.month]).date()

        date_difference = relativedelta.relativedelta(end_date, start_date)
        year_difference = date_difference.years
        add_months = 0
        if year_difference > 0:
            add_months = year_difference * 12
        date_difference = date_difference.months + add_months + 1

        if start_date and end_date:
            e_date = self.string_to_date(str(end_date))
            s_date = self.string_to_date(str(start_date))

            if self.key_account and self.key_account is not None:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_ka_export/' + str(s_date) + '/' + str(e_date) + '/' +
                           str(self.key_account.id) + '/' + str(date_difference),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_ka_export/' + str(s_date) + '/' + str(e_date) + '/' + str('none')
                           + '/' + str(date_difference),
                    'target': 'new'
                }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
