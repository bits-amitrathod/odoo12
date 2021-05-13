# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import operator


class TempProductList(models.Model):
    _name = 'quotation.product.list'
    _auto = False

    product_list = {}


    def init(self):
        self.init_table()

    def get_parent(self, partner_id):
        partner = self.env['res.partner'].search([('id', '=', partner_id), ])
        parent_partner_id = partner.id if partner.is_parent else partner.parent_id.id
        return parent_partner_id

    def init_table(self):
        #self.product_list.clear()
        temp_list = {}
        partner_id = self.env.context.get('quote_my_report_partner_id')
        if partner_id and partner_id is not None:
            #partner = self.env['res.partner'].search([('id', '=', partner_id), ])
            #parent_partner_id = partner.id
            partner_list = []
            #while not partner.is_parent:
            parent_partner_id = self.get_parent(partner_id)
            partner_list.append(parent_partner_id)
            #print(self.env['quotation.product.list'].search([('partner', '=', parent_partner_id)]))
            if self.product_list.get(parent_partner_id) and self.product_list.get(parent_partner_id) is not None:
                # print(self.product_list.get(parent_partner_id))
                self.product_list.pop(parent_partner_id)
            self.env.cr.execute("select id from res_partner where parent_id =" + str(parent_partner_id).replace(",)", ")"))
            chil_list = self.env.cr.dictfetchall()
            for i in chil_list:
                partner_list.append(i['id'])
            sql_query = """
                        SELECT  DISTINCT on (partn_name)
                        CONCAT(sale_order.partner_id, a.id) as partn_name,
                        ROW_NUMBER () OVER (ORDER BY sale_order.partner_id) as id,
                        sale_order.partner_id AS partner_id,
                        a.id AS product_id,
                        a.product_brand_id AS product_brand_id,      
                        null as min_expiration_date,
                        null as max_expiration_date,                  
                        1 as quantity                                     
                        FROM
                        sale_order
                        INNER JOIN sale_order_line
                        ON(
                        sale_order.id = sale_order_line.order_id and sale_order.partner_id in """+str(tuple(partner_list)).replace(",)", ")")+""")
                        INNER JOIN (select product_product.id , product_template.product_brand_id 
                                from product_product
                                INNER JOIN product_template
                                ON(product_product.product_tmpl_id = product_template.id  and
                                     product_template.actual_quantity > 0 and
                                     product_template.sale_ok = True)) as a              
                        ON(sale_order_line.product_id = a.id)
                        """
            groupby = """ 

                     group by partn_name, public.sale_order.partner_id,
                           a.id,
                           a.product_brand_id
                            """

            sql_query = sql_query + groupby

            self.env.cr.execute(sql_query)
            query_results = self.env.cr.dictfetchall()
            partner = self.env['res.partner'].search([('id', '=', parent_partner_id)])
            for query_result in query_results:
                product = self.env['product.product'].search([('id', '=', query_result['product_id'])])
                product_brand = self.env['product.brand'].search([('id', '=', query_result['product_brand_id'])])

                # get product expiration date
                self.env.cr.execute(
                    """
                    SELECT
                    sum(quantity), min(use_date), max(use_date)
                FROM
                    stock_quant
                INNER JOIN
                    stock_production_lot
                ON
                    (
                        stock_quant.lot_id = stock_production_lot.id)
                INNER JOIN
                    stock_location
                ON
                    (
                        stock_quant.location_id = stock_location.id)
                WHERE
                    stock_location.usage in('internal', 'transit') and stock_production_lot.product_id  = %s
                    """,
                    (query_result['product_id'],))
                result = self.env.cr.dictfetchone()

                if partner.property_product_pricelist.id:
                    price_list = partner.property_product_pricelist.get_product_price(
                        product, product.product_tmpl_id.actual_quantity, partner)
                else:
                    price_list = 0

                product_dict = {'product': product,
                                'partner': partner,
                                'partn_name': query_result['partn_name'],
                                'product_brand_name': product_brand.name,
                                'product_sku': product.product_tmpl_id.sku_code,
                                'min_expiration_date': result['min'],
                                'max_expiration_date': result['max'],
                                'price_list': price_list,
                                'quantity': query_result['quantity'],
                                'select': False}

                product_data = {product.id: product_dict}
                temp_list.update(product_data)
            customer_data={partner.id:temp_list}
            self.product_list.update(customer_data)
            print(customer_data)

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    def update_quantity(self, partner_id, product_id, set_qty, select):
        parent_partner_id = self.get_parent(partner_id)
        partner_product_list = self.product_list.get(parent_partner_id)

        if product_id is not None and product_id in partner_product_list.keys() and set_qty is not None:
            partner_product_list.get(product_id)['quantity'] = set_qty
        elif product_id is not None and product_id in partner_product_list.keys() and select is not None:
            partner_product_list.get(product_id)['select'] = select
        elif product_id is None and select is not None:
            for product_id in partner_product_list:
                partner_product_list.get(product_id)['select'] = select

    def get_product_list(self, partner_id):
        product_list_sorted = sorted(self.product_list[self.get_parent(partner_id)].items(), key=lambda x: (x[1]['product_brand_name'],
                                                                               x[1]['product_sku']))

        return self.product_list[self.get_parent(partner_id)], product_list_sorted
