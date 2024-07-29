# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class RevenueByBdPerAccount(models.Model):
    _name = 'report.bd.revenue.per.account'
    _description = "Revenue By Bd Per Account"
    _auto = False

    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    # date_order = fields.Datetime('Order Date')
    delivery_date = fields.Datetime('Delivery Date')
    # key_account = fields.Many2one('res.users', 'Key Account')
    customer = fields.Many2one('res.partner', 'Customer Name')
    business_development = fields.Many2one('res.users', 'Business Development')
    # product_tmpl_id = fields.Many2one('product.template', "Product")
    # qty_done = fields.Integer('Quantity')
    # unit_price = fields.Float('Unit Price')
    total_amount = fields.Float('Total')

    #  @api.model_cr
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
                        SO.user_id                          AS business_development,
                        SO.state                            AS status,                            
                        MAX(SP.date_done)                        AS delivery_date,
                        SUM(SOL.qty_delivered * SOL.price_reduce)  AS total_amount 

                       FROM public.sale_order SO

                       INNER JOIN 
                           public.sale_order_line SOL 
                       ON 
                           SO.id = SOL.order_id  
                       INNER JOIN 
                           (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin)

                          AS SP 
                       ON 
                           SO.id = SP.sale_id
                           
                        INNER JOIN 
                            public.res_partner RP
                        ON
                            SO.partner_id = RP.id AND (RP.is_wholesaler is NULL OR RP.is_wholesaler != TRUE) 
                            AND (RP.is_broker is NULL OR RP.is_broker != TRUE)

                        WHERE SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL


               """

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        compute_at = self.env.context.get('compute_at')
        salesperson_account_id = self.env.context.get('business_development')

        if compute_at == '1':
            if start_date and start_date is not None and end_date and end_date is not None:
                select_query = select_query + " AND SP.date_done BETWEEN '" + str(
                    start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"
        if salesperson_account_id:
            select_query = select_query + "AND SO.user_id = '" + str(salesperson_account_id) + "'"

        group_by = """
                    GROUP BY
                     SO.id
                        """

        sql_query = select_query + group_by

        self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code

class RevenueByBdPerAccountExport(models.TransientModel):
    _name = 'report.bd.revenue.per.account.export'
    _description = "Revenue By Bd Per Account Export"

    compute_at_date = fields.Selection([
        ('0', 'Show All'),
        ('1', 'Date Range ')
    ], string="Compute", default='0', help="Choose Show All or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)),
                             help="Choose a date to get the Revenu By Business Development at that  Start date")
    end_date = fields.Date('End Date', default=fields.date.today(),
                           help="Choose a date to get the Revenue By Business Development at that  End date")
    business_development = fields.Many2one('res.users', string="Business Development", index=True)

    def download_excel_bd_revenue(self):

        if self.compute_at_date == '1':
            e_date = self.string_to_date(str(self.end_date))
            e_date = e_date + datetime.timedelta(days=1)
            s_date = self.string_to_date(str(self.start_date))
            if self.business_development and self.business_development is not None:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_bd_per_account_export/' + str(s_date) + '/' + str(e_date) + '/' +
                           str(self.business_development.id),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_bd_per_account_export/' + str(s_date) + '/' + str(e_date) + '/' + str('none'),
                    'target': 'new'
                }
        else:
            if self.business_development:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_bd_per_account_export/' + str('all') + '/' + str('all') + '/' +
                           str(self.business_development.id),
                    'target': 'new'
                }
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/export/revenue_by_bd_per_account_export/' + str('all') + '/' + str('all') + '/' + str(
                        'none'),
                    'target': 'new'
                }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

