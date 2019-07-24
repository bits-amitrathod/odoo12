
from odoo import api, fields, models
from lxml import etree
from datetime import datetime
import pprint
import itertools


from dateutil.relativedelta import relativedelta


class TrendingReportListView(models.Model):
    _inherit = 'product.product'

    month1 = fields.Monetary(compute='_compute_sales_vals',currency_field='currency_id', store=False)
    month2 = fields.Monetary(compute='_compute_sales_vals',currency_field='currency_id', store=False)
    month3 = fields.Monetary(compute='_compute_sales_vals',currency_field='currency_id', store=False)
    month4 = fields.Monetary(compute='_compute_sales_vals',currency_field='currency_id', store=False)
    month5 = fields.Monetary(compute='_compute_sales_vals',currency_field='currency_id', store=False)
    month6 = fields.Monetary(compute='_compute_sales_vals',currency_field='currency_id', store=False)
    month1_quantity = fields.Integer(compute='_compute_sales_vals',  store=False)
    month2_quantity = fields.Integer(compute='_compute_sales_vals', store=False)
    month3_quantity = fields.Integer(compute='_compute_sales_vals', store=False)
    month4_quantity = fields.Integer(compute='_compute_sales_vals', store=False)
    month5_quantity = fields.Integer(compute='_compute_sales_vals', store=False)
    month6_quantity = fields.Integer(compute='_compute_sales_vals', store=False)
    total_sale=fields.Monetary(string="Total Sales", compute='_compute_sales_vals',currency_field='currency_id', store=False)
    total_quantity = fields.Integer(compute='_compute_sales_vals', store=False)
    product_uom_name=fields.Char(string="Product UOM",compute='_compute_sales_vals', store=False)


    # month_count = fields.Integer('Months Ago First Order', compute='_first_purchase_date', store=False)#'Months Ago First Order'
    # month_total = fields.Integer('Total Purchased Month', compute='_total_purchased_month', store=False)
    # trend_val = fields.Char('Trend', store=False,compute='_get_trend_value')
    # average_sale = fields.Monetary('Average',compute='_get_average_value', currency_field='currency_id', store=False)
    # total_sale = fields.Monetary('Total',compute='_get_total_value', currency_field='currency_id', store=False)
    currency_id = fields.Many2one("res.currency",compute='_compute_sales_vals', string="Currency", store=False)


    def _compute_sales_vals(self):
        popup = self.env['salesbymonth.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        if popup and popup.end_date and not popup.end_date is None:
            today = datetime.date(datetime.strptime(str(popup.end_date), "%Y-%m-%d"))
            today = today.replace(day=1)
            end_of_month = today + relativedelta(day=1,months=1, days=-1)
            sixth_month = (today - relativedelta(day=1, months=5))
            cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            for product in self:
                stock_move_list = self.env['stock.move'].search(
                    [('location_dest_id', '=', cust_location_id), ('state', '=', 'done'),('sale_line_id','!=',None),('product_id','=',product.id),('picking_id.date_done','>=',str(sixth_month)),('picking_id.date_done','<=',str(end_of_month))])
                for stock_move in stock_move_list:
                    product.currency_id=stock_move.sale_line_id.currency_id
                    scheduled_date=datetime.date(datetime.strptime(str(stock_move.picking_id.date_done).split(".")[0],"%Y-%m-%d %H:%M:%S"))
                    for stock_move_line in stock_move.move_line_ids:
                        product.product_uom_name=stock_move_line.product_uom_id.name
                        product.total_sale=product.total_sale + stock_move.sale_line_id.price_total
                        product.total_quantity=product.total_quantity+stock_move_line.qty_done
                        if ((scheduled_date.month == (today).month) and (scheduled_date.year == (today).year)):
                            product.month1 = product.month1 + (
                                        stock_move.sale_line_id.price_total )
                            product.month1_quantity =product.month1_quantity + int(stock_move_line.qty_done)
                        if ((scheduled_date.month == (today - relativedelta(months=1)).month) and (
                                scheduled_date.year == (today - relativedelta(months=1)).year)):
                            product.month2 = product.month2 + (
                                        stock_move.sale_line_id.price_total)
                            product.month2_quantity = product.month2_quantity + int(stock_move_line.qty_done)
                        if ((scheduled_date.month == (today - relativedelta(months=2)).month) and (
                                scheduled_date.year == (today - relativedelta(months=2)).year)):
                            product.month3 = product.month3 + (
                                        stock_move.sale_line_id.price_total)
                            product.month3_quantity = product.month3_quantity + int(stock_move_line.qty_done)
                        if ((scheduled_date.month == (today - relativedelta(months=3)).month) and (
                                scheduled_date.year == (today - relativedelta(months=3)).year)):
                            product.month4 = product.month4 + (
                                        stock_move.sale_line_id.price_total)
                            product.month4_quantity = product.month4_quantity + int(stock_move_line.qty_done)
                        if ((scheduled_date.month == (today - relativedelta(months=4)).month) and (
                                scheduled_date.year == (today - relativedelta(months=4)).year)):
                            product.month5 = product.month5 + (
                                        stock_move.sale_line_id.price_total )
                            product.month5_quantity = product.month5_quantity + int(stock_move_line.qty_done)
                        if((scheduled_date.month == (today - relativedelta(months=5)).month) and (scheduled_date.year ==  (today - relativedelta(months=5)).year)):
                            product.month6 = product.month6 + (stock_move.sale_line_id.price_total)
                            product.month6_quantity = product.month6_quantity + int(stock_move_line.qty_done)








    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        popup = self.env['salesbymonth.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        View = self.env['ir.ui.view']

        # Get the view arch and all other attributes describing the composition of the view
        result = self._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        # Override context for postprocessing
        if view_id and result.get('base_model', self._name) != self._name:
            View = View.with_context(base_model_name=result['base_model'])

        # Apply post processing, groups and modifiers etc...
        xarch, xfields = View.postprocess_and_fields(self._name, etree.fromstring(result['arch']), view_id)
        result['arch'] = xarch
        result['fields'] = xfields

        # Add related action information if aksed
        if toolbar:
            bindings = self.env['ir.actions.actions'].get_bindings(self._name)
            resreport = [action
                         for action in bindings['report']
                         if view_type == 'tree' or not action.get('multi')]
            resaction = [action
                         for action in bindings['action']
                         if view_type == 'tree' or not action.get('multi')]
            resrelate = []
            if view_type == 'form':
                resrelate = bindings['action_form_only']

            for res in itertools.chain(resreport, resaction):
                res['string'] = res['name']

            result['toolbar'] = {
                'print': resreport,
                'action': resaction,
                'relate': resrelate,
            }
            if popup and popup.end_date and not popup.end_date is None:
                today = datetime.date(datetime.strptime(str(popup.end_date), "%Y-%m-%d"))
                if(result['name']=="product.sale.by.count.view.list" ):
                    doc = etree.XML(result['arch'])
                    for node in doc.xpath("//field[@name='month6']"):
                        node.set('string', (today - relativedelta(months=5)).strftime('%b-%Y')+" (Sale)")
                    for node in doc.xpath("//field[@name='month5']"):
                        node.set('string', (today - relativedelta(months=4)).strftime('%b-%Y')+" (Sale)")
                    for node in doc.xpath("//field[@name='month4']"):
                        node.set('string', (today - relativedelta(months=3)).strftime('%b-%Y')+" (Sale)")
                    for node in doc.xpath("//field[@name='month3']"):
                        node.set('string', (today - relativedelta(months=2)).strftime('%b-%Y')+" (Sale)")
                    for node in doc.xpath("//field[@name='month2']"):
                        node.set('string', (today - relativedelta(months=1)).strftime('%b-%Y')+" (Sale)")
                    for node in doc.xpath("//field[@name='month1']"):
                        node.set('string', (today).strftime('%b-%Y')+" (Sale)")

                    result['arch'] = etree.tostring(doc, encoding='unicode')

                if(result['name']=="sales.by.month.form"):
                    doc = etree.XML(result['arch'])
                    for node in doc.xpath("//field[@name='month6']"):
                        node.set('string', (today - relativedelta(months=5)).strftime('%b-%Y') + " (Sale)")
                    for node in doc.xpath("//field[@name='month5']"):
                        node.set('string', (today - relativedelta(months=4)).strftime('%b-%Y') + " (Sale)")
                    for node in doc.xpath("//field[@name='month4']"):
                        node.set('string', (today - relativedelta(months=3)).strftime('%b-%Y') + " (Sale)")
                    for node in doc.xpath("//field[@name='month3']"):
                        node.set('string', (today - relativedelta(months=2)).strftime('%b-%Y') + " (Sale)")
                    for node in doc.xpath("//field[@name='month2']"):
                        node.set('string', (today - relativedelta(months=1)).strftime('%b-%Y') + " (Sale)")
                    for node in doc.xpath("//field[@name='month1']"):
                        node.set('string', (today).strftime('%b-%Y') + " (Sale)")
                    for node in doc.xpath("//field[@name='month6_quantity']"):
                        node.set('string', (today - relativedelta(months=5)).strftime('%b-%Y') + " (Quantity)")
                    for node in doc.xpath("//field[@name='month5_quantity']"):
                        node.set('string', (today - relativedelta(months=4)).strftime('%b-%Y') + " (Quantity)")
                    for node in doc.xpath("//field[@name='month4_quantity']"):
                        node.set('string', (today - relativedelta(months=3)).strftime('%b-%Y') + " (Quantity)")
                    for node in doc.xpath("//field[@name='month3_quantity']"):
                        node.set('string', (today - relativedelta(months=2)).strftime('%b-%Y') + " (Quantity)")
                    for node in doc.xpath("//field[@name='month2_quantity']"):
                        node.set('string', (today - relativedelta(months=1)).strftime('%b-%Y') + " (Quantity)")
                    for node in doc.xpath("//field[@name='month1_quantity']"):
                        node.set('string', (today).strftime('%b-%Y') + " (Quantity)")

                    result['arch'] = etree.tostring(doc, encoding='unicode')

        return result
