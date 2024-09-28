
import logging
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
import datetime
log = logging.getLogger(__name__)

class ReportCompareSaleByMonthWise(models.AbstractModel):
    _name = 'report.report_compare_sale_by_month.compsalebymonth_template'
    _description = "Report Compare Sale By Month Wise"

    def _get_report_values(self, docids, data=None):

        popup = self.env['compbysale.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        products = self.env['product.product'].search([('create_uid', '=', self._uid)], limit=1,)
        if popup.compute_at_date:
            date = datetime.datetime.strptime(str(popup.last_start_date), '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + \
                   datetime.datetime.strptime(str(popup.last_end_date), '%Y-%m-%d').strftime('%m/%d/%Y')+"        "+ \
                   datetime.datetime.strptime(str(popup.current_start_date), '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + \
                   datetime.datetime.strptime(str(popup.current_end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
            s_date = (fields.Datetime.from_string(popup.current_start_date).date())
            l_date = (fields.Datetime.from_string(popup.current_end_date).date())
            ps_date = (fields.Datetime.from_string(popup.last_start_date).date())
            pl_date = (fields.Datetime.from_string(popup.last_end_date).date())
        else:
            today=fields.date.today().replace(day=1)
            s_date = today
            l_date = (fields.date.today())
            ps_date = (today - relativedelta(day=1,months=1))
            pl_date = (ps_date+ relativedelta(day=1,months=1, days=-1))
            date= ps_date.strftime('%m/%d/%Y')+" - "+pl_date.strftime('%m/%d/%Y')+"       "+s_date.strftime('%m/%d/%Y') +" - "+ l_date.strftime('%m/%d/%Y')

        stock_location_id = self.env['stock.location'].search([('usage', '=', 'customer'), ]).id
        stock_move_line = self.env['stock.move.line'].search(
            [('state', 'in', ('done', 'partially_available')),('product_id.id','in',docids), ('location_dest_id.id', '=', stock_location_id),
             ('date', '>=', str(ps_date)), ('date', '<=', str(l_date))])

        filtered_by_current_month = list(filter(
            lambda x: fields.Datetime.from_string(x.date).date() >= s_date and fields.Datetime.from_string(
                x.date).date() <= l_date, stock_move_line))

        filtered_by_last_month = list(filter(
            lambda x: fields.Datetime.from_string(x.date).date() >= ps_date and fields.Datetime.from_string(
                x.date).date() <= pl_date, stock_move_line))
        product_dict = popup.addObject(filtered_by_current_month, filtered_by_last_month)
        products=self.fetch_data(product_dict,docids)
        return {'data': products, 'date': date}

    def fetch_data(self,dat,docids):
        dict=[]
        for order in docids:
            value = order in dat
            if value:
                object = dat[order]
                if int(object['current_month_total_qty']) > 0 or int(object['last_month_total_qty']) > 0:
                    # order.sku_name = dat[order.id].sku
                    dict.append(object)
        return dict