from numpy.lib.function_base import quantile
from odoo import models, fields, api, _
import datetime
# from odoo.tools.profiler import Profiler
# from stdnum.it.codicefiscale import values


# from stdnum.it.codicefiscale import values


class VendorOfferProductLineNew(models.Model):
    _inherit = "purchase.order.line"
    _description = "Vendor Offer Product line New"

    # New for Appraisal
    multiplier_app_new = fields.Many2one('multiplier.multiplier', string="Multiplier")
    product_qty_app_new = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    # sku_code = fields.Char('Product SKU', compute='onchange_product_id_vendor_offer', store=False)
    original_sku = fields.Char(string='Imported SKU')
    open_quotations_of_prod = fields.Float(string='Open Quotations', readonly=True, store=True) #set_line_initial_values ()
    average_aging = fields.Char(string='Average Aging', readonly=True, store=True) # assined in set_line_initial_values ()
    product_sales_amount_yr = fields.Float(string="Sales Amount Year", readonly=True, store=True) #  calculated using set_line_initial_values and get_product_sales_qty_or_amt_sum_by_days
    inv_ratio_90_days = fields.Float(string='INV Ratio', readonly=True, store=True) # get_inv_ratio_90_days and setting in set_line_initial_values()
    premium_product = fields.Boolean(string='Premium', readonly=True, store=True)
    consider_dropping_tier = fields.Boolean(string='CDT', readonly=True, store=True) # get_consider_dropping_tier and setting in set_line_initial_values()
    average_retail_last_year = fields.Float(string='Average Retail Last Year', readonly=True, store=True) # compute_average_retail and setting in set_line_initial_values()

    product_multiple_matches = fields.Boolean(string='Multiple Matches', store=True)
    list_contains_equip = fields.Boolean(string='Equipment', store=True)
    is_pddo = fields.Boolean(string='PDDO', default=False, readonly=True, store=True)
    product_note = fields.Text(string="Product Note", related='product_id.product_note', readonly=True)


    def get_line_average_aging(self):
        today_date = datetime.datetime.now()
        sql_query = """SELECT     Date(PUBLIC.stock_lot.create_date) AS create_date , 
                                                               Sum(PUBLIC.stock_quant.quantity)              AS quantity 
                                                    FROM       PUBLIC.product_product 
                                                    INNER JOIN PUBLIC.product_template 
                                                    ON         ( 
                                                                          PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id) 
                                                    INNER JOIN PUBLIC.stock_lot 
                                                    ON         ( 
                                                                          PUBLIC.stock_lot.product_id=PUBLIC.product_product.id ) 
                                                    INNER JOIN PUBLIC.stock_quant 
                                                    ON         ( 
                                                                          PUBLIC.stock_quant.lot_id=PUBLIC.stock_lot.id) 
                                                    INNER JOIN PUBLIC.stock_location 
                                                    ON         ( 
                                                                          PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id) 
                                                    INNER JOIN PUBLIC.stock_warehouse 
                                                    ON         ( 
                                                                          PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id, 
                                                                                                       PUBLIC.stock_warehouse.wh_output_stock_loc_id,
                                                                                                       wh_pack_stock_loc_id)) 
                                                    WHERE      PUBLIC.stock_quant.quantity>0 
                                                    AND        product_template.id = %s  AND stock_lot.use_date >= %s
                                                    GROUP BY   PUBLIC.stock_lot.create_date, 
                                                               PUBLIC.product_template.id
                                                               """
        self._cr.execute(sql_query, (self.product_id.product_tmpl_id.id, today_date))
        product_lot_list = self.env.cr.dictfetchall()
        sum_qty_day = 0
        total_quantity = 0
        for obj in product_lot_list:
            date_format = "%Y-%m-%d"
            today = fields.date.today().strftime('%Y-%m-%d')
            a = datetime.datetime.strptime(str(today), date_format)
            b = datetime.datetime.strptime(str(obj['create_date']), date_format)
            diff = a - b

            total_quantity = total_quantity + obj['quantity']
            sum_qty_day = sum_qty_day + (obj['quantity'] * diff.days)

        if total_quantity > 0:
            average_aging = int(round(sum_qty_day / total_quantity, 0))
        else:
            average_aging = 0

        return average_aging

    def get_line_average_retail_last_year(self,values={}):

        product_sales_count_yrs = values.get('product_sales_count_yrs', self.product_sales_count_yrs)
        product_sales_amount_yr = values.get('product_sales_amount_yr', self.product_sales_amount_yr)

        qty = product_sales_count_yrs
        price = self.product_unit_price
        if qty != 0 and price != 0:
            price_per_item = (product_sales_amount_yr / qty)
            average_retail_last_year = price_per_item / price
        else:
            average_retail_last_year = 0

        return average_retail_last_year

    def get_product_sales_qty_or_amt_sum_by_days(self, days, type='qty'):
        start_date = fields.Date.to_string(datetime.datetime.now() - datetime.timedelta(days=days))
        # cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
        idx = 0 if type == 'qty' else 1
        base_query = "select sum(sol.qty_delivered) as qty, sum(sol.price_subtotal) as amt " \
        "from sale_order AS so " \
        "JOIN sale_order_line AS sol " \
        "ON  so.id = sol.order_id " \
        "where sol.product_id = %s " \
        "AND sol.state in ('sale','done')" \
        "AND sol.qty_delivered>0"

        if days < 1000:
            self.env.cr.execute(base_query + " AND so.date_order>=%s", (self.product_id.id, start_date))
        else:
            self.env.cr.execute(base_query, [self.product_id.id])
        data = self.env.cr.fetchone()
        return (data[idx]) if data[idx] is not None else 0

    def get_quotations_count_by_product(self):
        # orders = self.env['sale.order'].search([('state', 'in', ['draft', 'sent'])])
        # quotations = orders.filtered(lambda order: self.id in order.order_line.mapped('product_id.id'))

        self.env.cr.execute("select "
                            "so.id, so.name "
                            "from sale_order so "
                            "right join sale_order_line sol "
                            "on so.id = sol.order_id and sol.product_id = " + str(self.product_id.id) +
                            " where so.state in ('draft','send')")
        data = self.env.cr.dictfetchall()

        return len(data) if data else 0

    def get_consider_dropping_tier(self, values={}):

        product_sales_count_90 = values.get('product_sales_count_90', self.product_sales_count_90)
        qty_in_stock = values.get('qty_in_stock', self.qty_in_stock)
        product_sales_count_yrs = values.get('product_sales_count_yrs', self.product_sales_count_yrs)

        if product_sales_count_90 != 0:
            condition = qty_in_stock / product_sales_count_90 > 4
        else:
            condition = False
        result = condition and product_sales_count_yrs >= qty_in_stock
        return result

    def get_inv_ratio_90_days(self,values={}):
        product_sales_count_90 = values.get('product_sales_count_90', self.product_sales_count_90)
        qty_in_stock = values.get('qty_in_stock', self.qty_in_stock)

        return qty_in_stock / product_sales_count_90 if product_sales_count_90 != 0 else 0

    def is_recalculate_multiplier(self):
        return False if self.multiplier else True


    def get_initial_values(self):

        if not self.id:
            return {}

        product_tier = self.product_id.product_tmpl_id.tier
        sku_code = self.product_id.product_tmpl_id.sku_code
        product_brand_id = self.product_id.product_tmpl_id.product_brand_id.id

        product_sales_count_month = self.get_product_sales_qty_or_amt_sum_by_days(30, 'qty')
        product_sales_count_90 = self.get_product_sales_qty_or_amt_sum_by_days(90, 'qty')
        product_sales_count_yrs = self.get_product_sales_qty_or_amt_sum_by_days(365, 'qty')
        product_sales_amount_yr = self.get_product_sales_qty_or_amt_sum_by_days(365, 'amt')
        product_sales_count = self.get_product_sales_qty_or_amt_sum_by_days(1001, 'qty')

        premium_product = self.product_id.premium
        qty_in_stock = self.product_id.actual_quantity
        open_quotations_of_prod = self.get_quotations_count_by_product()
        expired_inventory = self.get_expired_inventory_cal()
        average_aging = self.get_line_average_aging()

        values = {
            "product_tier" : product_tier,
            "sku_code" : sku_code,
            "product_brand_id" : product_brand_id,
            "product_qty_app_new" : 1,
            "product_qty" : 1,
            "product_sales_count_month" : product_sales_count_month,
            "product_sales_count_90" : product_sales_count_90,
            "product_sales_count_yrs" : product_sales_count_yrs,
            "product_sales_amount_yr": product_sales_amount_yr,
            "product_sales_count" : product_sales_count,
            'premium_product' : premium_product,
            "qty_in_stock" : qty_in_stock,
            "open_quotations_of_prod": open_quotations_of_prod,
            "expired_inventory": expired_inventory,
            "average_aging" : average_aging
        }

        consider_dropping_tier = self.get_consider_dropping_tier(values)
        inv_ratio_90_days = self.get_inv_ratio_90_days(values)
        is_pddo = True if product_sales_count_90 == 0 else False
        average_retail_last_year = self.get_line_average_retail_last_year()

        values.update({
            "consider_dropping_tier" : consider_dropping_tier,
            "inv_ratio_90_days" : inv_ratio_90_days,
            "is_pddo": is_pddo,
            "average_retail_last_year" : average_retail_last_year,
            "product_qty" :  self.product_qty_app_new,
        })
        return values


    def set_line_initial_values(self):
        values = self.get_initial_values()
        self.write(values)

    def get_multiplier_as_per_rule_and_data(self,values={}):
        qty_in_stock = values.get('qty_in_stock', self.qty_in_stock)
        product_sales_count = values.get('product_sales_count', self.product_sales_count)
        qty_sold_yr = values.get('product_sales_count_yrs', self.product_sales_count_yrs)
        tier = self.product_id.tier
        open_quotations_cnt = values.get('open_quotations_of_prod', self.open_quotations_of_prod)
        qty_sold_90_days = values.get('product_sales_count_90', self.product_sales_count_90)
        average_aging = values.get('average_aging', self.average_aging)
        inv_ratio_90_days = values.get('inv_ratio_90_days', self.inv_ratio_90_days)
        product_sales_total_amount_yr = values.get('product_sales_amount_yr', self.product_sales_amount_yr)
        PDDO = values.get('is_pddo', self.is_pddo)
        purchase_order = self.order_id
        multiplier = None

        if purchase_order.is_dynamic_tier_adjustment:
            if qty_in_stock == 0 and product_sales_count == 0:
                if 0 < open_quotations_cnt < 5:
                    multiplier = 'TIER 3'
                elif 5 <= open_quotations_cnt <= 15:
                    multiplier = 'T 2 GOOD - 35 PRCT'
                elif open_quotations_cnt > 15:
                    multiplier = 'T 1 GOOD - 45 PRCT'
            elif tier and tier.code == '1' and inv_ratio_90_days < 1 and not PDDO:
                if product_sales_total_amount_yr >= 100000 or open_quotations_cnt >= 20:
                    multiplier = 'PREMIUM - 50 PRCT'
            elif tier and tier.code == '1' and qty_in_stock == 0 and open_quotations_cnt >= 20:
                multiplier = 'PREMIUM - 50 PRCT'
            elif tier and tier.code == '2' and inv_ratio_90_days < 1 and not PDDO and open_quotations_cnt >= 10:
                multiplier = 'T 1 GOOD - 45 PRCT'
            elif (tier and tier.code == '2' and qty_in_stock == 0 and qty_sold_90_days > 0 and open_quotations_cnt >= 10):
                multiplier = 'T 1 GOOD - 45 PRCT'
            elif qty_sold_yr >= qty_in_stock > 0 and qty_sold_90_days == 0 and product_sales_count != 0 and int(average_aging) > 30:
                multiplier = 'TIER 3'
            elif qty_in_stock == 0 and qty_sold_yr == 0 and product_sales_count != 0 and open_quotations_cnt < 5:
                multiplier = 'TIER 3'

        if multiplier is None:

            threshold = self.env['vendor.threshold']
            t1 = threshold.search([('code', '=', 'T1')], limit=1)
            t2 = threshold.search([('code', '=', 'T2')], limit=1)
            t3 = threshold.search([('code', '=', 'T3')], limit=1)

            t1_overstock_threshold = t1.worth if t1 else 0
            t1_to_t3_threshold = t2.worth if t2 else 0
            t2_threshold = t3.worth if t3 else 0

            premium = self.product_id.premium

            if tier:
                if product_sales_count == 0:
                    multiplier = "NO HISTORY / EXPIRED"
                elif tier.code == '1' and qty_sold_yr <= qty_in_stock <= qty_sold_yr * t1_to_t3_threshold:
                    multiplier = "T 2 GOOD - 35 PRCT"
                elif qty_in_stock > qty_sold_yr * t1_overstock_threshold or (
                        qty_in_stock > qty_sold_yr * t2_threshold and tier.code == '2'):
                    multiplier = "TIER 3"
                elif premium:
                    multiplier = "PREMIUM - 50 PRCT"
                elif tier.code == '1':
                    multiplier = "T 1 GOOD - 45 PRCT"
                elif tier.code == '2':
                    multiplier = "T 2 GOOD - 35 PRCT"
                else:
                    multiplier = "OUT OF SCOPE"

        if multiplier is None:
            multiplier = self.get_default_multiplier()

        if multiplier and purchase_order.is_change_tier1_to_premium:
            multiplier = "PREMIUM - 50 PRCT"  if "T 1" in multiplier else multiplier


        multiplier_id = None
        if multiplier is not None:
            multiplier_id = self.env['multiplier.multiplier'].search([('name', '=', multiplier)], limit=1)

        return multiplier_id

    def get_default_multiplier(self):
        multiplier = None
        if self.multiplier is None:
            if self.product_id and self.product_id.tier and self.product_id.tier.code == '1':
                multiplier = 'T 1 GOOD - 45 PRCT'
            elif self.product_id and self.product_id.tier and self.product_id.tier.code == '2':
                multiplier = 'T 2 GOOD - 35 PRCT'
            elif self.product_id and self.product_id.tier and self.product_id.tier.code == '3':
                multiplier = 'name', '=', 'TIER 3'

        return multiplier

    def set_multiplier_as_per_rule_and_data(self):
        self.multiplier = self.get_multiplier_as_per_rule_and_data()

    def get_total_line_vendor(self):
        line = self
        taxes1 = line.taxes_id.compute_all(float(line.product_unit_price),
                                           line.order_id.currency_id,
                                           line.product_qty,
                                           product=line.product_id,
                                           partner=line.order_id.partner_id)

        taxes = line.taxes_id.compute_all(float(line.product_offer_price),
                                          line.order_id.currency_id,
                                          line.product_qty,
                                          product=line.product_id,
                                          partner=line.order_id.partner_id)

        values = {
            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
            'price_subtotal': taxes['total_excluded'],
            'price_total': taxes['total_included'],
            'price_unit': line.product_offer_price,

            'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
            'product_retail': taxes1['total_excluded'],
            'rt_price_total': taxes1['total_included'],
        }
        return values

    def overstock_threshold(self):
        threshold = self.env['vendor.threshold'].search([('code', '=', 'T1')], limit=1)
        threshold2 = self.env['vendor.threshold'].search([('code', '=', 'T2')], limit=1)
        threshold3 = self.env['vendor.threshold'].search([('code', '=', 'T3')], limit=1)
        last_year_sales_qty = self.product_sales_count_yrs
        qty_in_stock = self.qty_in_stock

        if threshold3 and (last_year_sales_qty * threshold3.worth) > qty_in_stock and 'T 1' in self.multiplier:
            self.multiplier = self.env['multiplier.multiplier'].search([('name', '=', 'TIER 3')], limit=1)
        elif threshold and (last_year_sales_qty * threshold.worth) > qty_in_stock and 'T 1' in self.multiplier:
            self.multiplier = self.env['multiplier.multiplier'].search([('name', '=', 'T 2 GOOD - 35 PRCT')], limit=1)

        if threshold2 and (last_year_sales_qty * threshold2.worth) > qty_in_stock and 'T 2' in self.multiplier:
            self.multiplier = self.env['multiplier.multiplier'].search([('name', '=', 'TIER 3')], limit=1)


    def set_line_other_values(self):
        values = self.get_total_line_vendor()
        self.write(values)

