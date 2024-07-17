# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging
import operator

_logger = logging.getLogger(__name__)


class TempProductList(models.Model):
    _name = 'quotation.product.list'
    _description = ""
    _auto = False

    product_list = {}


    def init(self):
        self.init_table()

    def get_parent(self, partner_id):
        partner = self.env['res.partner'].search([('id', '=', partner_id), ])
        parent_partner_id = None
        if partner:
            if partner.is_parent:
                parent_partner_id = partner.id
            elif partner.parent_id and partner.parent_id.id:
                parent_partner_id = partner.parent_id.id
            else:
                parent_partner_id = partner.id
        else:
            print('partner is inactive')

        # parent_partner_id = partner.id if partner.is_parent else partner.parent_id.id
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
                        null as str_max_date,                  
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
                                     product_template.sale_ok = True and product_template.is_published = True and
                                     product_template.active = True)
                                Where product_product.active = True and product_product.id NOT IN (Select product_id 
                                from public.exclude_product_in_stock where partner_id = """ + str(parent_partner_id) + """)) as a         
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
                    stock_lot
                ON
                    (
                        stock_quant.lot_id = stock_lot.id)
                INNER JOIN
                    stock_location
                ON
                    (
                        stock_quant.location_id = stock_location.id)
                WHERE
                    stock_location.usage in('internal', 'transit') and stock_lot.product_id  = %s
                    """,
                    (query_result['product_id'],))
                result = self.env.cr.dictfetchone()

                if partner.property_product_pricelist.id and product:
                    price_list_without_round_off = partner.property_product_pricelist._get_product_price(
                        product, product.product_tmpl_id.actual_quantity)
                    #price_list = float("{0:.2f}".format(price_list_without_round_off))
                    price_list = round(price_list_without_round_off,2)
                else:
                    if product.product_tmpl_id.list_price:
                        price_list = float("{0:.2f}".format(product.product_tmpl_id.list_price))
                    else:
                        price_list = product.product_tmpl_id.list_price

                str_date_cal = ''
                str_date_min = ''
                if (result['min'] is not None and result['max'] is not None) and \
                        ((result['max'] - result['min']).days > 365):
                    str_date_cal = '1 Year+'
                elif result['min'] is not None and result['max'] is not None:
                    str_date_cal = result['max'].strftime('%m/%d/%Y')

                if ((result['min'].date() > fields.Datetime.today().date())
                        and ((result['min'].date() - fields.Datetime.today().date()).days > 365)
                        and ((result['max'].date() - result['min'].date()).days > 365)):
                    str_date_min = '-'
                elif result['min'] is not None:
                    str_date_min = result['min'].strftime('%m/%d/%Y')

                company_fetch = self.env['res.company'].search([], limit=1, order="id desc")
                product_dict = {'product': product,
                                'partner': partner,
                                'partn_name': query_result['partn_name'],
                                'product_brand_name': product_brand.name,
                                'product_sku': product.product_tmpl_id.sku_code,
                                'min_expiration_date': result['min'],
                                'max_expiration_date': result['max'],
                                'str_max_date': str_date_cal,
                                'str_min_date': str_date_min,
                                'price_list': price_list,
                                'price_curr': company_fetch.currency_id,
                                'quantity': query_result['quantity'],
                                'select': False}

                product_data = {product.id: product_dict}
                temp_list.update(product_data)
            customer_data={partner.id:temp_list}
            self.product_list.update(customer_data)
        else:
            # This Code For only console error resolve purposr
            self.env.cr.execute('''
                         CREATE OR REPLACE VIEW %s AS (
                         SELECT  so.id AS id,
                                 so.name AS name
                         FROM sale_order so
                         )''' % (self._table)
                                )

    def set_empty_product_list(self, partner_id=None):
        #self.product_list.clear()
        temp_list = {}
        #partner_id = self.env.context.get('quote_my_report_partner_id')
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
                        null as str_max_date,                
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
                                     product_template.sale_ok = True and product_template.is_published = True and
                                     product_template.active = True)
                                Where product_product.active = True and product_product.id NOT IN (Select product_id 
                                from public.exclude_product_in_stock where partner_id = """ + str(parent_partner_id) + """)) as a         
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
                    stock_lot
                ON
                    (
                        stock_quant.lot_id = stock_lot.id)
                INNER JOIN
                    stock_location
                ON
                    (
                        stock_quant.location_id = stock_location.id)
                WHERE
                    stock_location.usage in('internal', 'transit') and stock_lot.product_id  = %s
                    """,
                    (query_result['product_id'],))
                result = self.env.cr.dictfetchone()

                if partner.property_product_pricelist.id and product:
                    price_list_without_round_off = partner.property_product_pricelist._get_product_price(
                        product, product.product_tmpl_id.actual_quantity)
                    #price_list = float("{0:.2f}".format(price_list_without_round_off))
                    price_list = round(price_list_without_round_off,2)
                else:
                    if product.product_tmpl_id.list_price:
                        price_list = float("{0:.2f}".format(product.product_tmpl_id.list_price))
                    else:
                        price_list = product.product_tmpl_id.list_price

                company_fetch = self.env['res.company'].search([], limit=1, order="id desc")
                str_date_cal = ''
                if (result['min'] is not None and result['max'] is not None) and\
                        ((result['max'] - result['min']).days > 365):
                    str_date_cal = '1 Year+'
                elif result['min'] is not None and result['max'] is not None:
                    str_date_cal = result['max'].strftime('%m/%d/%Y')

                product_dict = {'product': product,
                                'partner': partner,
                                'partn_name': query_result['partn_name'],
                                'product_brand_name': product_brand.name,
                                'product_sku': product.product_tmpl_id.sku_code,
                                'min_expiration_date': result['min'],
                                'max_expiration_date': result['max'],
                                'str_max_date': str_date_cal,
                                'price_list': price_list,
                                'price_curr': company_fetch.currency_id,
                                'quantity': query_result['quantity'],
                                'select': False}

                product_data = {product.id: product_dict}
                temp_list.update(product_data)
            customer_data={partner.id:temp_list}
            self.product_list.update(customer_data)
        else:
            # This Code For only console error resolve purposr
            self.env.cr.execute('''
                         CREATE OR REPLACE VIEW %s AS (
                         SELECT  so.id AS id,
                                 so.name AS name
                         FROM sale_order so
                         )''' % (self._table)
                                )

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

    def update_quantity(self, partner_id, product_id, set_qty, select):
        _logger.info('In update quantity method')
        _logger.info(set_qty)
        _logger.info(select)
        parent_partner_id = self.get_parent(partner_id)
        partner_product_list = self.product_list.get(parent_partner_id)
        _logger.info(partner_product_list)
        if partner_product_list:
            if product_id is not None and product_id in partner_product_list.keys() and set_qty is not None:
                partner_product_list.get(product_id)['quantity'] = set_qty
            elif product_id is not None and product_id in partner_product_list.keys() and select is not None:
                partner_product_list.get(product_id)['select'] = select
                _logger.info('select true set 1')
            elif product_id is None and select is not None:
                for product_id in partner_product_list:
                    partner_product_list.get(product_id)['select'] = select
                    _logger.info('select true set 2')

        _logger.info(partner_product_list)

    def update_quantity_from_list(self, partner_id, product_id, set_qty, select):
        _logger.info('- update_quote_my_report_json_list  update_quantity_from_list')
        parent_partner_id = self.get_parent(partner_id)
        _logger.info('- update_quote_my_report_json_list  partner_id  : %s', partner_id)
        _logger.info('- update_quote_my_report_json_list  parent_partner_id  : %s', parent_partner_id)
        _logger.info('- update_quote_my_report_json_list  self.product_list  : %s', self.product_list)
        if partner_id and partner_id is not None and len(self.product_list) == 0:
            self.set_empty_product_list(partner_id)
        partner_product_list = self.product_list.get(parent_partner_id)
        if partner_id and partner_id is not None and partner_product_list is None:
            self.set_empty_product_list(partner_id)
            partner_product_list = self.product_list.get(parent_partner_id)
        
        _logger.info('- update_quote_my_report_json_list  partner_product_list  : %s', partner_product_list)
        if partner_product_list:
            _logger.info('- update_quote_my_report_json_list')
            _logger.info('- update_quote_my_report_json_list  partner_product_list.keys()  : %s', partner_product_list.keys())
            _logger.info('- update_quote_my_report_json_list  product_id  : %s', product_id)
            _logger.info('- update_quote_my_report_json_list  set_qty  : %s', set_qty)
            _logger.info('- update_quote_my_report_json_list  select  : %s', select)
            if product_id is not None and product_id in partner_product_list.keys() and set_qty is not None:
                partner_product_list.get(product_id)['quantity'] = set_qty
                _logger.info('- update_quote_my_report_json_list  set_qty  done')
            if product_id is not None and product_id in partner_product_list.keys() and select is not None:
                partner_product_list.get(product_id)['select'] = select
                _logger.info('- update_quote_my_report_json_list  select  done')
            elif product_id is None and select is not None:
                for product_id in partner_product_list:
                    partner_product_list.get(product_id)['select'] = select
            _logger.info('- update_quote_my_report_json_list  partner_product_list  : %s', partner_product_list)

    def get_product_list(self, partner_id):
        _logger.info('update_quote_my_report_json_list In get_product_list -  partner_id : %s', str(partner_id))
        try:
            if partner_id and partner_id is not None and len(self.product_list) > 0:
                parent_id = self.get_parent(partner_id)
                _logger.info('update_quote_my_report_json_list In get_product_list - parent_id : %s', str(parent_id))
                _logger.info('update_quote_my_report_json_list In get_product_list - elf.product_list[parent_id] : %s',
                             self.product_list[parent_id])
                _logger.info('update_quote_my_report_json_list In get_product_list - '
                             'self.product_list[parent_id].items() : %s', self.product_list[parent_id].items())
                if parent_id is not None and len(self.product_list[parent_id]) > 0 and self.product_list[parent_id].items():
                    _logger.info('update_quote_my_report_json_list In get_product_list - product_list : %s', self.product_list[parent_id])
                    product_list_sorted = sorted(self.product_list[parent_id].items(),
                                            key=lambda x: (x[1]['product_brand_name'] if 'product_brand_name' in x[1] else "Test",
                                                            x[1]['product_sku'] if 'product_sku' in x[1] else "Test"))
                    _logger.info('update_quote_my_report_json_list In get_product_list - product_list_sorted : %s',
                                 product_list_sorted)
                    return self.product_list[parent_id], product_list_sorted
                else:
                    _logger.info('update_quote_my_report_json_list In get_product_list  -- else 212')
                    return [], []
            else:
                _logger.info('update_quote_my_report_json_list In get_product_list  -- else 215')
                return [], []
        except Exception as e:
            _logger.error(e)
