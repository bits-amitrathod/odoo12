# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools
from dateutil.relativedelta import relativedelta
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging
_logger = logging.getLogger(__name__)


class NewAccountByMonthByBd(models.Model):
    _name = 'report.bd.new.account'
    _description = "New Account By Month By Bd"
    _auto = False
    _order = 'business_development'

    onboard_date = fields.Datetime('Delivery Date')
    customer = fields.Many2one('res.partner', 'Customer Name')
    business_development = fields.Many2one('res.users', 'Business Development')

    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        business_development_id = self.env.context.get('business_development')

        today = start_date if start_date else fields.date.today()
        internal_date = (today - relativedelta(months=24))

        if start_date and end_date :
            select_query = """
                SELECT 
                    ROW_NUMBER () OVER (ORDER BY RPS.id)    AS id,
                    SOS.partner_id                          AS customer, 
                    SOS.user_id                             AS business_development, 
                    MIN(SPS.date_done)                      AS onboard_date
                FROM public.sale_order SOS 
                INNER JOIN 
                    public.res_partner RPS 
                ON 
                    SOS.partner_id = RPS.id AND (RPS.is_wholesaler is NULL OR RPS.is_wholesaler != TRUE) 
                    AND (RPS.is_broker is NULL OR RPS.is_broker != TRUE)
                INNER JOIN 
                    public.stock_picking SPS 
                ON 
                    SOS.id = SPS.sale_id AND SPS.picking_type_id = 5 AND SPS.state = 'done'
                
                WHERE SOS.user_id IS NOT NULL AND SOS.state NOT IN ('cancel', 'void') AND SOS.partner_id IN
                
                ((  SELECT 
                        DISTINCT (SO.partner_id) partner1
                    FROM 
                        public.sale_order SO
                    INNER JOIN 
                        public.stock_picking SP 
                    ON 
                        SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 AND
                                  
                   """
            select_query = select_query + " SP.date_done BETWEEN '" + str(start_date) + "'" + " AND '" + str(
                end_date) + "' " + """ WHERE SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                SELECT 
                    DISTINCT (SO.partner_id) partner
                FROM 
                    public.sale_order SO
                INNER JOIN 
                    public.stock_picking SP ON SO.id = SP.sale_id AND SP.state = 'done' AND 
                    SP.picking_type_id = 5 AND SP.date_done  BETWEEN ' """ + str(internal_date) + """'""" + """ AND ' """ + str(today) + """'
                    WHERE SO.state NOT IN ('cancel', 'void'))) UNION ALL ("""

            select_query = select_query + """ 
            SELECT 
                DISTINCT (SO.partner_id) partner1
            FROM 
                public.sale_order SO 
            WHERE SO.id IN (
                SELECT SO.id
                FROM 
                    public.sale_order SO
                INNER JOIN 
                    public.stock_picking SP 
                ON 
                    SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 AND SP.date_done BETWEEN ' """ + \
                    str(start_date) + "' " + " AND '" + str(end_date) + \
                    """ ' AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                WHERE SO.partner_id IN (
                        SELECT id
                        FROM public.res_partner RP
                        WHERE RP.reinstated_date IS NOT NULL AND RP.reinstated_date BETWEEN ' """ + \
                        str(start_date) + "'" + " AND '" + str(end_date) + "' ) ) AND SO.partner_id NOT IN ("

            select_query = select_query + """ 
                SELECT 
                    DISTINCT (SO.partner_id) partner
                FROM 
                    public.sale_order SO        
                WHERE SO.id IN (        
                        Select SO.id
                        From public.sale_order SO
                        INNER JOIN public.stock_picking SP 
                        ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 AND SP.date_done <= ' """ + \
                        str(start_date) + "' " + \
                        """ AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                        WHERE SO.partner_id IN (
                                SELECT id 
                                FROM public.res_partner RP
                                WHERE RP.reinstated_date IS NOT NULL AND RP.reinstated_date <= '""" + str(start_date) +\
                                "' ) ) ))) AND SPS.date_done" \
                                " >= COALESCE(RPS.reinstated_date, RPS.create_date) AND SPS.date_done BETWEEN '" + \
                                str(start_date) + "'" + " AND '" + str(end_date) + "' "

            if business_development_id:
                select_query = select_query + "AND SOS.user_id = '" + str(business_development_id) + "'"

            group_by = """ GROUP BY RPS.id, SOS.partner_id, SOS.user_id  
                            ORDER BY RPS.name """

            select_query = select_query + group_by

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

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code

class NewAccountByMonthByBdExport(models.TransientModel):
    _name = 'report.bd.new.account.export'
    _description =  "New Account By Month By Bd Export"

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)),
                             help="Choose a date to get the New Account By Month By Business Development at that  Start date")
    end_date = fields.Date('End Date', default=fields.date.today(),
                           help="Choose a date to get the New Account By Month By Business Development at that  End date")
    business_development = fields.Many2one('res.users', string="Business Development", index=True)

    def download_excel_bd_new_account(self):

        e_date = self.string_to_date(str(self.end_date))
        e_date = e_date + datetime.timedelta(days=1)
        s_date = self.string_to_date(str(self.start_date))

        if self.business_development and self.business_development is not None:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/new_account_by_month_by_bd_export/' + str(s_date) + '/' + str(e_date) + '/' +
                       str(self.business_development.id),
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/new_account_by_month_by_bd_export/' + str(s_date) + '/' + str(e_date) + '/' + str('none'),
                'target': 'new'
            }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

