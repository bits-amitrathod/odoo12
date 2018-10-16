# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class mtd_sales(models.Model):

    _name = 'mtd_sales'
    _auto = False

    day_of_month = fields.Integer('Day')
    amount_total = fields.Float('Amount')

    @api.model_cr
    def init(self):
        # self.init_table()
        pass

    @api.model_cr
    def init_table(self):
        tools.drop_view_if_exists(self._cr, 'mtd_sales')

        month = self.env.context.get('month')
        year = self.env.context.get('year')

        if not year is None and not month is None:
            # sql_query = "CREATE VIEW mtd_sales AS ( " + self.select_query() + self.from_clause() + self.where_clause(
            #     year,
            #     month) + " )"

            # sql_query = """ CREATE VIEW mtd_sales AS (
            #             SELECT
            #                 ROW_NUMBER () OVER (ORDER BY EXTRACT(day FROM  so.confirmation_date)) as id,
            #                 EXTRACT(day FROM  so.confirmation_date) as day_of_month,
            #                 SUM(so.amount_total) as amount_total
            #             FROM
            #                 sale_order so
            #             WHERE
            #                 EXTRACT(month FROM  so.confirmation_date) = """ + str(month) + """ AND
            #                 EXTRACT(year FROM so.confirmation_date) = """ + str(year) + """ AND
            #                 so.state = 'sale' GROUP BY EXTRACT(day FROM  so.confirmation_date) )"""

            sql_query = """ CREATE VIEW mtd_sales AS ( 
                SELECT ROW_NUMBER () OVER (ORDER BY day_of_month) as id,  day_of_month as day_of_month,  CASE WHEN q.amount_total IS NULL THEN 0 ELSE q.amount_total END as amount_total
FROM    generate_series(1, 31) as day_of_month LEFT JOIN ( SELECT                              
                            EXTRACT(day FROM  so.confirmation_date) as day_from_date, 
                            SUM(so.amount_total) as amount_total 
                        FROM 
                            sale_order so
                        WHERE 
                            EXTRACT(month FROM  so.confirmation_date) = """ + str(month) + """ AND 
                            EXTRACT(year FROM so.confirmation_date) = """ + str(year) + """  AND so.state = 'sale'                           
                       GROUP BY EXTRACT(day FROM  so.confirmation_date)) q                       
                       ON q.day_from_date = day_of_month
                )
            """
            self._cr.execute(sql_query)

    def select_query(self):
        return """ SELECT 
        ROW_NUMBER () OVER (ORDER BY EXTRACT(day FROM  so.confirmation_date)) as id,
        EXTRACT(day FROM so.confirmation_date) as day_of_month,  
        so.amount_total as amount_total """

    def from_clause(self):
        return """
            FROM sale_order so 
        """

    def where_clause(self, year, month):
        _logger.info('year: %r, month: %r', str(year), str(month))
        return """
            WHERE 
        EXTRACT(month FROM  so.confirmation_date) = """ + str(month) + """ AND 
        EXTRACT(year FROM so.confirmation_date) = """ + str(year) + """ AND 
        so.state = 'sale'
        """
