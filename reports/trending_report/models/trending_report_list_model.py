from docutils.nodes import field

from odoo import api, fields, models
from lxml import etree
from datetime import datetime
from odoo.osv import expression
import itertools
import logging
_logger = logging.getLogger(__name__)


from dateutil.relativedelta import relativedelta


class TrendingReportListView(models.Model):
    _inherit = 'res.partner'

    month1 = fields.Monetary(currency_field='currency_id', store=False)
    month2 = fields.Monetary(currency_field='currency_id', store=False)
    month3 = fields.Monetary(currency_field='currency_id', store=False)
    month4 = fields.Monetary(currency_field='currency_id', store=False)
    month5 = fields.Monetary(currency_field='currency_id', store=False)
    month6 = fields.Monetary(currency_field='currency_id', store=False)
    month7 = fields.Monetary(currency_field='currency_id', store=False)
    month8 = fields.Monetary(currency_field='currency_id', store=False)
    month9 = fields.Monetary(currency_field='currency_id', store=False)
    month10 = fields.Monetary(currency_field='currency_id', store=False)
    month11 = fields.Monetary(currency_field='currency_id', store=False)
    month12 = fields.Monetary(currency_field='currency_id', store=False)
    month_count = fields.Integer('Months Ago First Order', compute='_first_purchase_date', store=False)#'Months Ago First Order'
    month_total = fields.Integer('Total Purchased Month', compute='_total_purchased_month', store=False)
    trend_val = fields.Char('Trend', store=False,compute='_get_trend_value')
    average_sale = fields.Monetary('Average',compute='_get_average_value', currency_field='currency_id', store=False)
    total_sale = fields.Monetary('Total',compute='_get_total_value', currency_field='currency_id', store=False)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)

    def _search_month_total(self, operator, value):
        la = self.search(['&', ('customer_rank', '>', 0), ('parent_id', '=', False)]).filtered(lambda x: x.month_total > 0 )
        return [('id', '=', [x.id for x in la])]

    def _compute_commercial_entity(self):
        if 'action' in self.env.context.keys():
            for customer in self:
                customer.commercial_entity = customer.parent_id.name if customer.parent_id else customer.name
        else:
            self.commercial_entity = None

    commercial_entity = fields.Char(string="Commercial Entity", compute='_compute_commercial_entity', store=False)


    #@api.onchange('')
    def _compute_sales_vals(self):
        if 'action' in self.env.context.keys():
            if 's_date' in self.env.context:
                start_date = self.string_to_date(self.env.context['s_date'])
            else:
                popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                start_date = self.string_to_date(popup.start_date)
            if 'code' in self.env.context:
                code = self.env.context['code']
            else:
                popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                code = int(popup.code)

            for customer in self:
                groupby_dict_month = {}
                sale_orders = self.env['sale.order'].search([('partner_id', '=', customer.id), ('state', '=', 'sale')])
                groupby_dict_month['data'] = sale_orders
                for sale_order in groupby_dict_month['data']:
                    confirmation_date=datetime.date(datetime.strptime(str(sale_order.date_order).split(".")[0],"%Y-%m-%d %H:%M:%S"))
                    if((confirmation_date.month == (start_date - relativedelta(months=5)).month) and (confirmation_date.year ==  (start_date - relativedelta(months=5)).year)):
                        customer.month6 = customer.month6 + sale_order.amount_total
                    if((confirmation_date.month == (start_date - relativedelta(months=4)).month) and (confirmation_date.year ==  (start_date - relativedelta(months=4)).year)):
                        customer.month5 = customer.month5 + sale_order.amount_total
                    if((confirmation_date.month == (start_date - relativedelta(months=3)).month) and (confirmation_date.year ==  (start_date - relativedelta(months=3)).year)):
                        customer.month4 = customer.month4 + sale_order.amount_total
                    if((confirmation_date.month == (start_date - relativedelta(months=2)).month) and (confirmation_date.year ==  (start_date - relativedelta(months=2)).year)):
                        customer.month3 = customer.month3 + sale_order.amount_total
                    if((confirmation_date.month == (start_date - relativedelta(months=1)).month) and (confirmation_date.year ==  (start_date - relativedelta(months=1)).year)):
                        customer.month2 = customer.month2 + sale_order.amount_total
                    if((confirmation_date.month == (start_date).month) and (confirmation_date.year ==  (start_date).year)):
                        customer.month1 = customer.month1 + sale_order.amount_total
                    if(code==12):
                        if ((confirmation_date.month == (start_date - relativedelta(months=11)).month) and (confirmation_date.year == (start_date - relativedelta(months=11)).year)):
                            customer.month12 = customer.month12 + sale_order.amount_total
                        if ((confirmation_date.month == (start_date - relativedelta(months=10)).month) and (confirmation_date.year == (start_date - relativedelta(months=10)).year)):
                            customer.month11 = customer.month11 + sale_order.amount_total
                        if ((confirmation_date.month == (start_date - relativedelta(months=9)).month) and (confirmation_date.year == (start_date - relativedelta(months=9)).year)):
                            customer.month10 = customer.month10 + sale_order.amount_total
                        if ((confirmation_date.month == (start_date - relativedelta(months=8)).month) and (confirmation_date.year == (start_date - relativedelta(months=8)).year)):
                            customer.month9 = customer.month9 + sale_order.amount_total
                        if ((confirmation_date.month == (start_date - relativedelta(months=7)).month) and (confirmation_date.year == (start_date - relativedelta(months=7)).year)):
                            customer.month8 = customer.month8 + sale_order.amount_total
                        if ((confirmation_date.month == (start_date - relativedelta(months=6)).month) and (confirmation_date.year == (start_date - relativedelta(months=6)).year)):
                            customer.month7 = customer.month7 + sale_order.amount_total



    @api.onchange('trend_val')
    def _get_total_value(self):
        if 'action' in self.env.context.keys():
            if 'code' in self.env.context:
                code = self.env.context['code']
            else:
                popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                code = int(popup.code)
            for customer in self:
                customer.total_sale=customer.month1+customer.month2+customer.month3+customer.month4+customer.month5+customer.month6
                if(code==12):
                    customer.total_sale=customer.total_sale+customer.month7+customer.month8+customer.month9+customer.month10+customer.month11+customer.month12
        else:
            self.total_sale = 0

    @api.onchange('month_count')
    def _first_purchase_date(self):
        if 'action' in self.env.context.keys():
            self._compute_sales_vals()
            for customer in self:
                if(self.get_day_from_purchase(customer.id)):
                    customer.month_count = self.get_day_from_purchase(customer.id) / 30
                else:
                    customer.month_count=0
        else:
            self.month_count = 0
            _logger.info("trending _first_purchase_date-->  else")



    def get_day_from_purchase(self,customer_id):
        if 'action' in self.env.context.keys():
            if 's_date' in self.env.context:
                start_date = self.string_to_date(self.env.context['s_date'])
            else:
                popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                start_date = self.string_to_date(popup.start_date)
            groupby_dict_month = {}
            min = None
            sale_orders = self.env['sale.order'].search([('partner_id', '=', customer_id), ('state', '=', 'sale')])
            groupby_dict_month['data'] = sale_orders
            for sale_order in groupby_dict_month['data']:
                if (min == None):
                    min = sale_order.date_order
                elif (min > sale_order.date_order):
                    min = sale_order.date_order
            if (min):
                in_days = (start_date - datetime.date(datetime.strptime(str(min).split(".")[0], "%Y-%m-%d %H:%M:%S"))).days
                return in_days
            else:
                return None
        else:
            return None


    @api.onchange('month_total')
    def _total_purchased_month(self):
        if 'action' in self.env.context.keys():
            if 's_date' in self.env.context:
                start_date = self.env.context['s_date']
            else:
                popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                start_date = popup.start_date
            for customer in self:
                groupby_dict_month = {}
                sale_order_dict= {}
                sale_orders = self.env['sale.order'].search([('partner_id', '=', customer.id), ('state', '=', 'sale'), ('date_order','<=', start_date)])
                sale_order_dict['data'] = sale_orders
                for sale_order in sale_order_dict['data']:
                    confirmation_date = datetime.date(datetime.strptime(str(sale_order.date_order).split(".")[0], "%Y-%m-%d %H:%M:%S"))
                    count=0
                    if (groupby_dict_month.get(confirmation_date.strftime('%b-%Y'))):
                        count=groupby_dict_month[confirmation_date.strftime('%b-%Y')]
                        count=count+1
                        groupby_dict_month[confirmation_date.strftime('%b-%Y')]=count
                    else:
                        groupby_dict_month[confirmation_date.strftime('%b-%Y')]=1
                customer.month_total = len(groupby_dict_month)
            else:
                customer.month_total = 0

    @api.onchange('total_sale')
    def _get_trend_value(self):
        if 'action' in self.env.context.keys():
            for customer in self:
                if(customer.average_sale <= customer.month1):
                    customer.trend_val='UP'
                elif(customer.average_sale > customer.month1):
                    customer.trend_val = 'DOWN'
                if (customer.month1 == 0):
                    customer.trend_val = 'NO SALE'
        else:
            self.trend_val = 0


    # @api.onchange('average_sale')
    def _get_average_value(self):
        if 'action' in self.env.context.keys():
            if 'code' in self.env.context:
                code=self.env.context['code']
            else:
                popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                code = int(popup.code)
            for customer in self:
                if(customer.month_count>=code):
                    if code > 0:
                        customer.average_sale = (customer.total_sale / code)
                    else:
                        customer.average_sale = 1
                elif(self.get_day_from_purchase(customer.id)):
                    if (self.get_day_from_purchase(customer.id)/30 > 1):
                        customer.average_sale=(customer.total_sale *30 / self.get_day_from_purchase(customer.id))
                    else:
                        customer.average_sale=customer.total_sale
                else:
                    customer.average_sale = customer.total_sale
            else:
                self.average_sale = 0


    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):

        self.check_access_rights('read')
        view = self.env['ir.ui.view'].sudo().browse(view_id)

        # Get the view arch and all other attributes describing the composition of the view
        result = self._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        # Override context for postprocessing
        if view_id and result.get('base_model', self._name) != self._name:
            view = view.with_context(base_model_name=result['base_model'])

        # Apply post processing, groups and modifiers etc...
        xarch, xfields = view.postprocess_and_fields(etree.fromstring(result['arch']), model=self._name)
        result['arch'] = xarch
        result['fields'] = xfields

        # Add related action information if aksed
        if toolbar:
            vt = 'list' if view_type == 'tree' else view_type
            bindings = self.env['ir.actions.actions'].get_bindings(self._name)
            resreport = [action
                         for action in bindings['report']
                         if vt in (action.get('binding_view_types') or vt).split(',')]
            resaction = [action
                         for action in bindings['action']
                         if vt in (action.get('binding_view_types') or vt).split(',')]

            result['toolbar'] = {
                'print': resreport,
                'action': resaction,
            }

            if result['name'] == "purchase.vendor.view.list":
                doc = etree.XML(result['arch'])
                if 's_date' in self.env.context:
                    start_date = self.string_to_date(self.env.context['s_date'])
                else:
                    popup = self.env['popup.trending.report'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
                    start_date = self.string_to_date(popup.start_date)

                for node in doc.xpath("//field[@name='month1']"):
                    node.set('string', (start_date).strftime('%b-%y'))
                for node in doc.xpath("//field[@name='month2']"):
                    node.set('string', (start_date - relativedelta(months=1)).strftime('%b-%y'))
                for node in doc.xpath("//field[@name='month3']"):
                    node.set('string', (start_date - relativedelta(months=2)).strftime('%b-%y'))
                for node in doc.xpath("//field[@name='month4']"):
                    node.set('string', (start_date - relativedelta(months=3)).strftime('%b-%y'))
                for node in doc.xpath("//field[@name='month5']"):
                    node.set('string', (start_date - relativedelta(months=4)).strftime('%b-%y'))
                for node in doc.xpath("//field[@name='month6']"):
                    node.set('string', (start_date - relativedelta(months=5)).strftime('%b-%y'))
                if self.env.context['code'] == 12:
                    for node in doc.xpath("//field[@name='month7']"):
                        node.set('string', (start_date - relativedelta(months=6)).strftime('%b-%y'))
                    for node in doc.xpath("//field[@name='month8']"):
                        node.set('string', (start_date - relativedelta(months=7)).strftime('%b-%y'))
                    for node in doc.xpath("//field[@name='month9']"):
                        node.set('string', (start_date - relativedelta(months=8)).strftime('%b-%y'))
                    for node in doc.xpath("//field[@name='month10']"):
                        node.set('string', (start_date - relativedelta(months=9)).strftime('%b-%y'))
                    for node in doc.xpath("//field[@name='month11']"):
                        node.set('string', (start_date - relativedelta(months=10)).strftime('%b-%y'))
                    for node in doc.xpath("//field[@name='month12']"):
                        node.set('string', (start_date - relativedelta(months=11)).strftime('%b-%y'))
                result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

    @staticmethod
    def string_to_date(date_string):
        if date_string:
            return datetime.strptime(str(date_string), "%Y-%m-%d").date()
        else:
            return datetime.today().date()
