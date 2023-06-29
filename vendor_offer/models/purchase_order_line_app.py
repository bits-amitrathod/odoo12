from odoo import models, fields, api, _
import datetime


class VendorOfferProductLineNew(models.Model):
    _inherit = "purchase.order.line"
    _description = "Vendor Offer Product line New"

    # New for Appraisal
    multiplier_app_new = fields.Many2one('multiplier.multiplier', string="Multiplier")
    product_qty_app_new = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    original_sku = fields.Char(string='Imported SKU')
    open_quotations_of_prod = fields.Float(string='Open Quotations', readonly=True, store=True) #get_quotations_count_by_product
    average_aging = fields.Char(string='Average Aging', readonly=True, store=True) # assined in compute_new_fields_vendor_line
    product_sales_amount_yr = fields.Float(string="Sales Amount Year", readonly=True, store=True) #  calculated using compute_new_fields_vendor_line and get_product_sales_qty_or_amt_sum_by_days
    inv_ratio_90_days = fields.Float(string='INV Ratio', readonly=True, store=True) # get_inv_ratio_90_days
    premium_product = fields.Boolean(string='Premium', readonly=True, store=True)
    consider_dropping_tier = fields.Boolean(string='CDT', readonly=True, store=True) # get_consider_dropping_tier
    average_retail_last_year = fields.Float(string='Average Retail Last Year', readonly=True, store=True) # compute_average_retail
    dont_recalculate_offer_price = fields.Boolean(string='Do not Recalculate Price', store=True)
    product_multiple_matches = fields.Boolean(string='Multiple Matches', store=True)
    list_contains_equip = fields.Boolean(string='Equipment', store=True)

    def compute_new_fields_vendor_line(self):
        for line in self:
            result1 = {}
            if not line.id:
                return result1

            ''' sale count will show only done qty '''

            today_date = datetime.datetime.now()
            last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))

            ''' state = sale condition added in all sales amount to match the value of sales amount to 
            clients PPvendorpricing file '''

            sale_all_query = """SELECT  sum(sol.price_total) as total_sales
            from  product_product pp 
             INNER JOIN sale_order_line sol ON sol.product_id=pp.id 
             INNER JOIN product_template pt ON  pt.id=pp.product_tmpl_id
             INNER JOIN sale_order so ON so.id=sol.order_id
             INNER JOIN stock_picking sp ON sp.sale_id =so.id
             where pp.id =%s and sp.date_done>= %s and sp.date_done<=%s and sp.location_dest_id = 9
              group by sp.state"""

            self.env.cr.execute(sale_all_query, (line.product_id.id, last_yr, today_date))

            sales_all_value = 0
            sales_all_val = self.env.cr.fetchone()
            if sales_all_val and sales_all_val[0] is not None:
                sales_all_value = sales_all_value + float(sales_all_val[0])
            line.product_sales_amount_yr = sales_all_value

            sql_query = """SELECT     Date(PUBLIC.stock_production_lot.create_date) AS create_date , 
                                                       Sum(PUBLIC.stock_quant.quantity)              AS quantity 
                                            FROM       PUBLIC.product_product 
                                            INNER JOIN PUBLIC.product_template 
                                            ON         ( 
                                                                  PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id) 
                                            INNER JOIN PUBLIC.stock_production_lot 
                                            ON         ( 
                                                                  PUBLIC.stock_production_lot.product_id=PUBLIC.product_product.id ) 
                                            INNER JOIN PUBLIC.stock_quant 
                                            ON         ( 
                                                                  PUBLIC.stock_quant.lot_id=PUBLIC.stock_production_lot.id) 
                                            INNER JOIN PUBLIC.stock_location 
                                            ON         ( 
                                                                  PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id) 
                                            INNER JOIN PUBLIC.stock_warehouse 
                                            ON         ( 
                                                                  PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id, 
                                                                                               PUBLIC.stock_warehouse.wh_output_stock_loc_id,
                                                                                               wh_pack_stock_loc_id)) 
                                            WHERE      PUBLIC.stock_quant.quantity>0 
                                            AND        product_template.id = %s  AND stock_production_lot.use_date >= %s
                                            GROUP BY   PUBLIC.stock_production_lot.create_date, 
                                                       PUBLIC.product_template.id
                                                       """
            self._cr.execute(sql_query, (line.product_id.product_tmpl_id.id, today_date))
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
                line.average_aging = int(round(sum_qty_day / total_quantity, 0))
            else:
                line.average_aging = 0

            line.open_quotations_of_prod = line.get_quotations_count_by_product()
            line.inv_ratio_90_days = line.get_inv_ratio_90_days()
            line.premium_product = line.product_id.premium
            line.consider_dropping_tier = line.get_consider_dropping_tier()
            line.qty_in_stock = line.product_id.qty_available


    def copy_product_qty_column(self):
        for line in self:
            line.product_qty = line.product_qty_app_new

    def compute_total_line_vendor(self):
        for line in self:
            taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                               line.product_qty, product=line.product_id,
                                               partner=line.order_id.partner_id)

            taxes = line.taxes_id.compute_all(float(line.product_offer_price), line.order_id.currency_id,
                                              line.product_qty, product=line.product_id,
                                              partner=line.order_id.partner_id)

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_subtotal': taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_unit': line.product_offer_price,

                'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                'product_retail': taxes1['total_excluded'],
                'rt_price_total': taxes1['total_included'],
            })

    def is_recalculate_multiplier(self):
        return False if self.multiplier else True

    def get_product_sales_qty_or_amt_sum_by_days(self, days, type='qty'):
        start_date = fields.Date.to_string(datetime.datetime.now() - datetime.timedelta(days=days))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
        idx = 0 if type == 'qty' else 1
        base_query = "select sum(sol.qty_delivered) as qty, sum(sol.price_subtotal) as amt " \
        "from sale_order AS so " \
        "JOIN sale_order_line AS sol " \
        "ON  so.id = sol.order_id " \
        "where sol.product_id = %s " \
        "AND sol.state in ('sale','done')" \
        "AND so.date_order>=%s" \
        "AND sol.qty_delivered>0"
        self.env.cr.execute(base_query, (self.product_id.id, start_date))
        data = self.env.cr.fetchone()
        return int(data[idx]) if data[idx] is not None else 0

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

    def get_consider_dropping_tier(self):
        if self.product_sales_count_90 != 0:
            condition = self.qty_in_stock / self.product_sales_count_90 > 4
        else:
            condition = False

        result = condition and self.product_sales_count_yrs >= self.qty_in_stock

    def get_inv_ratio_90_days(self):
        return self.qty_in_stock / self.product_sales_count_90 if self.product_sales_count_90 != 0 else 0

    def multiplier_adjustment_criteria(self):
        for po_line in self:
            qty_in_stock = po_line.qty_in_stock
            product_sales_count = po_line.product_sales_count  # qty_sold_all
            qty_sold_yr = po_line.product_sales_count_yrs
            tier = po_line.product_id.tier
            open_quotations_cnt = po_line.get_quotations_count_by_product()
            qty_sold_90_days = po_line.product_sales_count_90
            average_aging = po_line.product_id.average_aging
            inv_ratio_90_days = po_line.get_inv_ratio_90_days()
            product_sales_total_amount_yr = po_line.get_product_sales_qty_or_amt_sum_by_days(365, 'amt')
            multiplier = 'TIER 3'
            if qty_in_stock == 0 and product_sales_count == 0:
                if 0 < open_quotations_cnt < 5:
                    multiplier = 'TIER 3'
                elif 5 <= open_quotations_cnt <= 15:
                    multiplier = 'T 2 Good – 35 PRCT'
                elif open_quotations_cnt > 15:
                    multiplier = 'T 1 Good – 45 PRCT'
            elif tier and tier.code == '1' and inv_ratio_90_days < 1:
                if product_sales_total_amount_yr >= 100000 or open_quotations_cnt >= 20 or qty_in_stock == 0:
                    multiplier = 'Premium – 50 PRCT'
            elif tier and tier.code == '2' and inv_ratio_90_days < 1:
                if open_quotations_cnt >= 10 or (qty_in_stock == 0 and qty_sold_90_days > 0):
                    multiplier = 'T 1 Good – 45 PRCT'
            elif qty_sold_yr >= qty_in_stock > 0 and qty_sold_90_days == 0 and product_sales_count == 0 and average_aging > 30:
                multiplier = 'TIER 3'
            elif qty_in_stock == 0 and qty_sold_yr == 0 and product_sales_count == 0 and open_quotations_cnt < 5:
                multiplier = 'TIER 3'

            # Change TIER 3 To multiplier this is for only testing purpose
            # multiplier = 'TIER 3'
            po_line.multiplier = self.env['multiplier.multiplier'].search([('name', '=', multiplier)], limit=1)

    def no_tier_multiplier_adjustment_criteria(self):
        for po_line in self:
            qty_in_stock = po_line.qty_in_stock
            product_sales_count = po_line.product_sales_count  # qty_sold_all
            qty_sold_yr = po_line.product_sales_count_yrs
            tier = po_line.product_id.tier

            threshold = self.env['vendor.threshold']
            t1 = threshold.search([('code', '=', 'T1')], limit=1)
            t2 = threshold.search([('code', '=', 'T2')], limit=1)
            t3 = threshold.search([('code', '=', 'T3')], limit=1)

            t1_overstock_threshold = t1.worth if t1 else 0
            t1_to_t3_threshold = t2.worth if t2 else 0
            t2_threshold = t3.worth if t3 else 0

            premium = po_line.product_id.premium

            if tier:
                if product_sales_count == 0:
                    return "NO History / Expired"
                elif tier.code == '1' and qty_sold_yr <= qty_in_stock <= qty_sold_yr * t1_to_t3_threshold:
                    return "T 2 Good - 35 PRCT"
                elif qty_in_stock > qty_sold_yr * t1_overstock_threshold or (
                        qty_in_stock > qty_sold_yr * t2_threshold and tier.code == '2'):
                    return "Tier 3"
                elif premium:
                    return "Premium - 50 PRCT"
                elif tier.code == '1':
                    return "T 1 Good – 45 PRCT"
                elif tier.code == '2':
                    return "T 2 Good – 35 PRCT"
                else:
                    return "OUT OF SCOPE"
            else:
                return "OUT OF SCOPE"

            po_line.multiplier = self.env['multiplier.multiplier'].search([('name', '=', multiplier)], limit=1)

    def set_values(self):
        self.product_sales_count_month = self.get_product_sales_qty_or_amt_sum_by_days(30, 'qty')
        self.product_sales_count_90 = self.get_product_sales_qty_or_amt_sum_by_days(90, 'qty')
        self.product_sales_count_yrs = self.get_product_sales_qty_or_amt_sum_by_days(365, 'qty')

    def compute_average_retail(self):
        qty = self.get_product_sales_qty_or_amt_sum_by_days(365, 'qty')
        price = self.product_unit_price
        if qty != 0 and price != 0:
            price_per_item = (self.get_product_sales_qty_or_amt_sum_by_days(365, 'amt') / qty)
            self.average_retail_last_year = price_per_item / price
        else:
            self.average_retail_last_year = 0


    def upgrade_multiplier_tier1_to_premium(self):
        if self.multiplier and self.multiplier.name and "T 1" in self.multiplier.name:
            mul = self.env['multiplier.multiplier'].search([('name', '=', 'Premium – 50 PRCT')], limit=1)
            self.multiplier = mul if mul else None
