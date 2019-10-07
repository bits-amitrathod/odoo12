import time

from odoo import api, fields, models, _
import datetime
from dateutil.relativedelta import relativedelta

class comparebymonth(object):
    product_name = ''
    current_month_total_qty = 0
    current_month_total_amount = 0
    last_month_total_qty = 0
    last_month_total_amount = 0
    sku=''

class DateGen:

    def getFirstOfMonth(self):
        dtDateTime = fields.date.today()
        ddays = int(dtDateTime.strftime("%d")) - 1  # days to subtract to get to the 1st
        delta = datetime.timedelta(days=ddays)  # create a delta datetime object
        return dtDateTime - delta

    def getLastOfMonth(self):
        dtDateTime = fields.date.today()
        next_month = dtDateTime.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
        return next_month - datetime.timedelta(days=next_month.day)

    def getFirstDayOfLastMonth(self):
        dtDateTime = self.getLastDayOfLastMonth()
        ddays = int(dtDateTime.strftime("%d")) - 1  # days to subtract to get to the 1st
        delta = datetime.timedelta(days=ddays)  # create a delta datetime object
        return dtDateTime - delta

    def getLastDayOfLastMonth(self):
        dtDateTime = self.getFirstOfMonth()
        ddays = int(dtDateTime.strftime("%d"))  # days to subtract to get to the 1st
        delta = datetime.timedelta(days=ddays)  # create a delta datetime object
        return dtDateTime - delta


class DiscountSummaryPopUp(models.TransientModel):
    _name = 'compbysale.popup'
    _description = 'Compare Sale By Month'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    date_gen = DateGen()
    dat=fields.defaultdict
    current_start_date = fields.Date('Current month Start Date', default=date_gen.getFirstOfMonth())
    current_end_date = fields.Date('Current month End Date', default=date_gen.getLastOfMonth())

    last_start_date = fields.Date('Last Month Start Date',default=date_gen.getFirstDayOfLastMonth())
    last_end_date = fields.Date('Last Month End Date', default=date_gen.getLastDayOfLastMonth())

    def open_table(self):
        tree_view_id = self.env.ref('report_compare_sale_by_month.list_view').id
        form_view_id = self.env.ref('product.product_normal_form_view').id

        sale_orders = self.env['sale.order'].search([('state','in',('sale','done'))])
        if self.compute_at_date:
            s_date = (fields.Datetime.from_string(self.current_start_date).date())
            l_date = (fields.Datetime.from_string(self.current_end_date).date())
            ps_date =(fields.Datetime.from_string( self.last_start_date).date())
            pl_date = (fields.Datetime.from_string(self.last_end_date).date())
        else :
            today = fields.date.today().replace(day=1)
            s_date = today
            l_date = (fields.date.today())
            ps_date = (today - relativedelta(day=1, months=1))
            pl_date = (ps_date + relativedelta(day=1, months=1, days=-1))


        stock_location_id=  self.env['stock.location'].search([('usage', '=', 'customer'),]).id
        stock_move_line = self.env['stock.move.line'].search(
            [ ('state', 'in', ('done', 'partially_available')),('location_dest_id.id','=',stock_location_id), ('date', '>=', str(ps_date)),('date','<=',str(l_date))])

        filtered_by_current_month = list(filter(
            lambda x: fields.Datetime.from_string(x.date).date() >= s_date and fields.Datetime.from_string(
                x.date).date() <= l_date, stock_move_line))

        filtered_by_last_month = list(filter(
            lambda x: fields.Datetime.from_string(x.date).date() >= ps_date and fields.Datetime.from_string(
                x.date).date() <= pl_date, stock_move_line))
        self.dat= self.addObject(filtered_by_current_month, filtered_by_last_month)


        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Compare Sales By Month'),
            'res_model': 'product.product',
            'context': {'dat': self.dat},
            'domain': [('id','in',list(self.dat.keys()))],
        }
        return action



    @api.multi
    def addObject(self, filtered_by_current_month, filtered_by_last_month):
        product_dict = {}
        product_ids=[]
        for record in filtered_by_current_month:
            if int(record.qty_done) > 0:
                if int(record.product_id.id) in product_dict:
                    data = product_dict[int(record.product_id.id)]
                    data['current_month_total_qty'] = data['current_month_total_qty'] + record.qty_done
                    data['current_month_total_amount'] = data['current_month_total_amount'] + (record.move_id.sale_line_id.price_total)
                    # data.location = stock_move_line.location_id.name
                    data['sku_code'] = record.product_id.product_tmpl_id.sku_code
                    product_dict[int(record.product_id.id)] = data
                else:
                    object = self.comparebymonth()
                    object['current_month_total_qty'] = record.qty_done
                    object['current_month_total_amount'] = record.move_id.sale_line_id.price_total
                    object['product_name']= record.product_id.name
                    object['sku_code'] = record.product_id.product_tmpl_id.sku_code
                    product_dict[int(record.product_id.id)] = object

        for record in filtered_by_last_month:
                if int(record.qty_done) > 0:
                    if int(record.product_id.id) in product_dict:
                        data = product_dict[int(record.product_id.id)]
                        data['last_month_total_qty']= data['last_month_total_qty'] + record.qty_done
                        data['last_month_total_amount'] = data['last_month_total_amount'] + record.move_id.sale_line_id.price_total
                        # data.location = stock_move_line.location_id.name
                        data['sku_code'] = record.product_id.product_tmpl_id.sku_code
                        product_dict[int(record.product_id.id)] = data
                    else:
                        object = self.comparebymonth()
                        object['last_month_total_qty' ]= record.qty_done
                        object['last_month_total_amount'] = record.move_id.sale_line_id.price_total
                        object['product_name'] = record.product_id.name
                        object['currency_symbol'] = record.product_id.currency_id.symbol
                        # object.location = stock_move_line.location_id.name
                        object['sku_code'] = record.product_id.product_tmpl_id.sku_code
                        product_dict[int(record.product_id.id)] = object
        return product_dict

    def comparebymonth(self):
        return {'product_name':"","current_month_total_qty":0,"current_month_total_amount":0,"last_month_total_qty":0,"last_month_total_amount":0,'sku_code':'','currency_symbol':""}