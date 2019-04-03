
from odoo import api, models
import datetime
#from reports.report_custom_product_catalog.models.catalog import InventoryCustomProductPopUp


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.catalog_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        popup = self.env['popup.custom.product.catalog'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        context = {}
        if popup.start_date or popup.end_date:
            product_list = self.fetchData(popup)
            context = {'production_lot_ids': product_list[0][1]}
        return {'data': self.env['product.product'].with_context(context).browse(docids)}

    def fetchData(self,ctx):
        sql_query = """select array_agg(product_id), json_object_agg(product_id, id) from stock_production_lot 
        where """
        if ctx.end_date and ctx.start_date:
            e_date = datetime.datetime.strptime(str(ctx.end_date), "%Y-%m-%d")
            sql_query = sql_query + """ use_date>=date(%s)  and  use_date<=date(%s)"""
            ctx._cr.execute(sql_query, (str(ctx.start_date), str(e_date),))
        elif ctx.start_date:
            sql_query = sql_query + """ use_date>=date(%s) """
            ctx._cr.execute(sql_query, (str(ctx.start_date),))
        elif ctx.end_date:
            e_date = datetime.datetime.strptime(str(ctx.end_date), "%Y-%m-%d")
            e_date = e_date + datetime.timedelta(days=1)
            sql_query = sql_query + """ use_date<=date(%s)"""
            ctx._cr.execute(sql_query, (str(e_date),))

        return ctx._cr.fetchall()

class ReportProductWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.product_catalog_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.product'].browse(docids)}
