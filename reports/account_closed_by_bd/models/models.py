# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from dateutil.relativedelta import relativedelta
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class AccountClosedByBd(models.Model):
    _name = 'report.bd.account.closed'
    _auto = False

    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    delivery_date = fields.Datetime('Delivery Date')
    state = fields.Char('Status')
    customer = fields.Many2one('res.partner', 'Customer Name')
    business_development = fields.Many2one('res.users', 'Business Development')
    total_amount = fields.Float('Total', digits=dp.get_precision('Product Price'))
    currency_id = fields.Many2one('res.currency', string='Currency')

    invoice_date = fields.Date('Invoice Date')
    date_of_first_order = fields.Date('Date of First Order')

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        # business_development_id = self.env.context.get('business_development')
        # key_account_id = self.env.context.get('key_account')

        if start_date and end_date:
            select_query = """
                SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id, 
                        so.id                               AS sale_order_id, 
                        so.partner_id                       AS customer, 
                        so.user_id                          AS business_development,
                        so.account_manager                  AS key_account,
                        so.state                            AS state,
                        MAX(SPS.date_done)                  AS delivery_date, 
                        rp.user_id                          AS customer_business_development,
                        rp.account_manager_cust             AS customer_key_account,
                        ai.invoice_date                     AS invoice_date, 
                        CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                        CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
                        SUM(SOL.qty_delivered * SOL.price_reduce)                   AS total_amount, 
                        X.months                            AS months,
                        ai.currency_id                      AS currency_id,
                        X.first_occurence                   AS date_of_first_order
                FROM public.sale_order so
                INNER JOIN
                   (
                    (SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                            DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                        FROM public.sale_order sos
                        INNER JOIN 
                            public.account_move aii ON sos.name = aii.invoice_origin
                            and aii.invoice_date > '""" + str(end_date) + """' 
                        GROUP BY sos.partner_id )
                        
                        UNION
                        
                        ( SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                            DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                        FROM public.sale_order sos 
                        INNER JOIN public.res_partner rep ON sos.partner_id= rep.id 
                        INNER JOIN public.account_move aii ON sos.name = aii.invoice_origin 
                        where rep.reinstated_date > ' """ + str(end_date) + """ ' and rep.reinstated_date is not null
                       
                        and  aii.invoice_date > ' """ + str(end_date) + """ '  GROUP BY sos.partner_id )
                        
                    ) X
                        ON so.partner_id = X.partner_id
                    INNER JOIN 
                        public.account_move ai ON so.name = ai.invoice_origin AND ai.state in ('posted')
                    INNER JOIN 
                        public.res_partner rp ON so.partner_id = rp.id
                        
                    INNER JOIN public.sale_order_line SOL ON so.id = SOL.order_id 
                    INNER JOIN 
                    (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 
                    AND state = 'done' ORDER BY origin) AS SPS 
                    ON so.id = SPS.sale_id
                    INNER JOIN  public.product_product  pp on SOL.product_id = pp.id 
                    INNER JOIN  public.product_template  pt on pp.product_tmpl_id = pt.id and pt.type!='service'
                
                WHERE so.invoice_status = 'invoiced'                
                   """

            select_query = select_query + " AND SPS.date_done >= COALESCE(rp.reinstated_date, ai.invoice_date,rp.create_date)" \
                                          " AND SPS.date_done BETWEEN '" + str(end_date) + "' " + " AND '" + str(
                start_date) + "' AND SPS.date_done <= (COALESCE(rp.reinstated_date, ai.invoice_date,rp.create_date) + " \
                              "INTERVAL '1 year')  "

            business_development_id = self.env.context.get('business_development')

            if business_development_id:
                select_query = select_query + "AND so.user_id = '" + str(business_development_id) + "'"

            group_by = """ GROUP BY so.id, SPS.date_done, SOL.currency_id,rp.user_id, rp.account_manager_cust,
              X.months  ,X.first_occurence ,ai.invoice_date,ai.state,ai.currency_id  """

            select_query = select_query + group_by

            order_by = " ORDER BY ai.invoice_date asc"

            select_query = select_query + order_by

            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )")
        else:
            # This Code For only console error resolve purposr
            self.env.cr.execute('''
                             CREATE OR REPLACE VIEW %s AS (
                             SELECT  so.id AS id,
                                     so.name AS name
                             FROM sale_order so
                             )''' % (self._table)
                                )

    def init_table_backup(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')

        if start_date and end_date:
            select_query = """
                SELECT 
                    ROW_NUMBER () OVER (ORDER BY SOS.id)    AS id,
                    SOS.id                                  AS sale_order_id,
                    SOS.partner_id                          AS customer, 
                    SOS.user_id                             AS business_development, 
                    MAX(SPS.date_done)                      AS delivery_date, 
                    SOS.state                               AS state,
                    SUM(SOL.qty_delivered * SOL.price_reduce) AS total_amount,
                    SOL.currency_id                         AS currency_id
                FROM public.sale_order SOS
                INNER JOIN public.sale_order_line SOL ON SOS.id = SOL.order_id 
                INNER JOIN public.res_partner RPS ON SOS.partner_id = RPS.id AND 
                (RPS.is_wholesaler is NULL OR RPS.is_wholesaler != TRUE) AND (RPS.is_broker is NULL OR RPS.is_broker != TRUE)
                INNER JOIN 
                (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin) AS SPS 
                ON SOS.id = SPS.sale_id
                WHERE SOS.state NOT IN ('cancel', 'void') AND SOS.user_id IS NOT NULL AND SOS.partner_id IN 
                ((SELECT DISTINCT (SO.partner_id) partner1
                FROM public.sale_order SO
                INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
                WHERE """

            select_query = select_query + " SP.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
                start_date) + "' " + """ AND SP.state = 'done'
                AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                    SELECT DISTINCT (SO.partner_id) partner
                    FROM public.sale_order SO
                    INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
                    WHERE """

            select_query = select_query + " SP.date_done <= '" + str(end_date) + "' " \
                           + """ AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')
                ))UNION ALL
                (SELECT DISTINCT (SO.partner_id) partner1
                FROM public.sale_order SO
                INNER JOIN public.stock_picking SP ON SO.id IN (
                    Select SO.id
                    From public.sale_order SO
                    INNER JOIN public.stock_picking SP 
                    ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 
                                  AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                    WHERE SO.partner_id IN (
                            SELECT id
                            FROM public.res_partner RP
                            WHERE RP.reinstated_date IS NOT NULL AND """

            select_query = select_query + " RP.reinstated_date BETWEEN '" + str(end_date) + "'" + " AND '" + str(
                start_date) + "' )) WHERE " + " SP.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
                start_date) + "' " + """ AND SP.state = 'done' AND SP.picking_type_id = 5 
                AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                        SELECT DISTINCT (SO.partner_id) partner
                        FROM public.sale_order SO        
                        INNER JOIN public.stock_picking SP ON SO.id IN (        
                                Select SO.id
                                From public.sale_order SO
                                INNER JOIN public.stock_picking SP 
                                ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 
                                              AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                                WHERE SO.partner_id IN (
                                        SELECT id 
                                        FROM public.res_partner RP
                                        WHERE RP.reinstated_date IS NOT NULL AND 
    
            """

            select_query = select_query + " RP.reinstated_date <= '" + str(end_date) + "' ) ) WHERE SP.date_done <= '" + str(end_date) +" ' " \
                                          " AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')))) "

            select_query = select_query + " AND SPS.date_done >= COALESCE(RPS.reinstated_date, RPS.create_date) " \
                                          " AND SPS.date_done BETWEEN '" + str(end_date) + "' " + " AND '" + str(start_date) + "' AND SPS.date_done <= (COALESCE(RPS.reinstated_date, RPS.create_date) + INTERVAL '1 year')  "

            business_development_id = self.env.context.get('business_development')

            if business_development_id:
                select_query = select_query + "AND SOS.user_id = '" + str(business_development_id) + "'"

            group_by = """ GROUP BY SOS.id, SPS.date_done, SOL.currency_id """

            select_query = select_query + group_by

            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )")
        else:
            # This Code For only console error resolve purposr
            self.env.cr.execute('''
                         CREATE OR REPLACE VIEW %s AS (
                         SELECT  so.id AS id,
                                 so.name AS name
                         FROM sale_order so
                         )''' % (self._table,)
                                )

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code

class AccountClosedByBdExport(models.TransientModel):
    _name = 'report.bd.account.closed.export'

    start_date = fields.Date('Start Date', default=fields.date.today(), required=True,
                             help="Choose a date to get the Revenue From Accounts Closed In 12 Months By BD at that End date")

    business_development = fields.Many2one('res.users', string='Business Development', index=True)

    delivery_start_date = fields.Date('Revenue Start Date')
    delivery_end_date = fields.Date('Revenue End Date')

    def download_excel_bd_account_closed(self):

        s_date = self.string_to_date(str(self.start_date))
        e_date = s_date - datetime.timedelta(days=365)
        e_date_from_first = datetime.date(e_date.year, e_date.month, 1)
        s_date = s_date + datetime.timedelta(days=1)

        if self.delivery_end_date:
            updated_delivery_end_date = self.string_to_date(str(self.delivery_end_date)) # + datetime.timedelta(days=1)

        if self.business_development and self.delivery_start_date and self.delivery_end_date:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/account_closed_by_bd_export/' + str(s_date) + '/' + str(e_date_from_first) + '/' +
                            str(self.business_development.id) + '/' + str(self.delivery_start_date) + '/' +
                            str(updated_delivery_end_date),
                'target': 'new'
            }
        elif self.delivery_start_date and self.delivery_end_date:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/account_closed_by_bd_export/' + str(s_date) + '/' + str(e_date_from_first) + '/' + str('none') +
                       '/' + str(self.delivery_start_date) + '/' + str(updated_delivery_end_date),
                'target': 'new'
            }

        elif self.business_development and self.business_development is not None:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/account_closed_by_bd_export/' + str(s_date) + '/' + str(e_date_from_first) + '/' +
                           str(self.business_development.id) + '/' + str('none') + '/' + str('none'),
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/account_closed_by_bd_export/' + str(s_date) + '/' + str(e_date_from_first) + '/' + str('none')
                       + '/' + str('none') + '/' + str('none'),
                'target': 'new'
            }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

