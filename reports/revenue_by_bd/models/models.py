# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class RevenueByBd(models.Model):
    _name = 'report.bd.revenue'
    _auto = False

    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    # date_order = fields.Datetime('Order Date')
    delivery_date = fields.Datetime('Delivery Date')
    state = fields.Char('Status')
    # key_account = fields.Many2one('res.users', 'Key Account')
    customer = fields.Many2one('res.partner', 'Customer Name')
    business_development = fields.Many2one('res.users', 'Business Development')
    # qty_done = fields.Integer('Quantity')
    # unit_price = fields.Float('Unit Price')
    total_amount = fields.Float('Total')
    currency_id = fields.Many2one('res.currency', string='Currency')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
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
                 INNER JOIN public.res_partner RPS ON SOS.partner_id = RPS.id
                 INNER JOIN public.stock_picking SPS ON SOS.id = SPS.sale_id AND SPS.picking_type_id = 5 AND SPS.state = 'done'
                 WHERE SOS.state NOT IN ('cancel', 'void') AND SOS.user_id IS NOT NULL AND SOS.partner_id IN 
                 ((SELECT DISTINCT (SO.partner_id) partner1
                 FROM public.sale_order SO
                 INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
                 WHERE """

            select_query = select_query + " SP.date_done BETWEEN '" + str(start_date) + "'" + " AND '" + str(
                end_date) + "' " + """ AND SP.state = 'done'
                 AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                     SELECT DISTINCT (SO.partner_id) partner
                     FROM public.sale_order SO
                     INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
                     WHERE """

            select_query = select_query + " SP.date_done <= '" + str(start_date) + "' " \
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

            select_query = select_query + " RP.reinstated_date BETWEEN '" + str(start_date) + "'" + " AND '" + str(
                end_date) + "' )) WHERE " + " SP.date_done BETWEEN '" + str(start_date) + "'" + " AND '" + str(
                end_date) + "' " + """ AND SP.state = 'done' AND SP.picking_type_id = 5 
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

            select_query = select_query + " RP.reinstated_date <= '" + str(
                start_date) + "' ) ) WHERE SP.date_done <= '" + str(end_date) + " ' " \
                                                                              " AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')))) "

            select_query = select_query + " AND SPS.date_done >= COALESCE(RPS.reinstated_date, RPS.create_date) " \
                                          " AND SPS.date_done BETWEEN '" + str(start_date) + "' " + " AND '" + str(
                end_date) + "' "


            business_development_id = self.env.context.get('business_development')


            if business_development_id:
                select_query = select_query + "AND SOS.user_id = '" + str(business_development_id) + "'"


            group_by = """ GROUP BY SOS.id, SPS.date_done, SOL.currency_id """

            sql_query = select_query + group_by

            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")


    @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code

class RevenueByBdExport(models.TransientModel):
    _name = 'report.bd.revenue.export'

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)),
                             help="Choose a date to get the Revenu By Business Development at that  Start date")
    end_date = fields.Date('End Date', default=fields.date.today(),
                           help="Choose a date to get the Revenue By Business Development at that  End date")
    business_development = fields.Many2one('res.users', string="Business Development", index=True)

    def download_excel_bd_revenue(self):

        e_date = self.string_to_date(str(self.end_date))
        e_date = e_date + datetime.timedelta(days=1)
        s_date = self.string_to_date(str(self.start_date))

        if self.business_development and self.business_development is not None:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/revenue_by_bd_export/' + str(s_date) + '/' + str(e_date) + '/' +
                       str(self.business_development.id),
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/revenue_by_bd_export/' + str(s_date) + '/' + str(e_date) + '/' + str('none'),
                'target': 'new'
            }


    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

