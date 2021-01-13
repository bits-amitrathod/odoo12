# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class TempProductList(models.Model):
    _name = 'quotation.product.list'
    _auto = False

    product = fields.Many2one('product.product', string='Product')
    partner = fields.Many2one('res.partner', string="Partner")
    product_brand_id = fields.Many2one('product.brand', string='Manufacturer')
    quantity = fields.Integer(string='Quantity')
    min_expiration_date = fields.Date("Min Expiration Date", compute='_calculate_max_min_lot_expiration')
    max_expiration_date = fields.Date("Max Expiration Date")
    price_list = fields.Float("Sales Price", compute='_calculate_max_min_lot_expiration')
    partn_name = fields.Char()

    # _sql_constraints = [
    #     ('product_uniq', 'unique(product, partner)', 'product must be unique per partner!'),
    # ]

    @api.multi
    def _calculate_max_min_lot_expiration(self):
        for record in self:
            # record.actual_quantity = record.product_tmpl_id.actual_quantity
            if record.partner.property_product_pricelist.id:
                record.price_list = record.partner.property_product_pricelist.get_product_price(
                    record.product, record.product.product_tmpl_id.actual_quantity, record.partner)
            else:
                record.price_list = 0

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
                (record.product.id,))
            query_result = self.env.cr.dictfetchone()
            record.min_expiration_date = fields.Date.from_string(query_result['min'])
            record.max_expiration_date = fields.Date.from_string(query_result['max'])

    @api.model_cr
    def init(self):
        print('In init')
        self.init_table()

    def init_table(self):
        print('In table')
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))
        partner_id = self.env.context.get('quote_my_report_partner_id')
        if partner_id and partner_id is not None:
            sql_query = """
                        SELECT  DISTINCT on (partn_name)
                        CONCAT(sale_order.partner_id, product_product.id) as partn_name,
                        ROW_NUMBER () OVER (ORDER BY sale_order.partner_id) as id,
                        sale_order.partner_id AS partner,
                        product_product.id AS product,
                        product_template.product_brand_id,
                        null as min_expiration_date,
                        null as max_expiration_date,
                        1 as quantity                                     
                        FROM
                        sale_order
                        INNER JOIN
                        sale_order_line
                        ON(
                        sale_order.id = sale_order_line.order_id)
                        INNER JOIN
                        product_product
                        ON
                        (
                        sale_order_line.product_id = product_product.id)
                        INNER JOIN
                        product_template
                        ON
                        (
                        product_product.product_tmpl_id = product_template.id  and  product_template.actual_quantity > 0 and 
                        product_template.sale_ok = True)
                        
                        """
            where = """
                    where 
                    sale_order.partner_id = 
                """ + str(partner_id)

            groupby = """
                    
                     group by partn_name, public.sale_order.partner_id,
                            public.product_product.id,
                            public.product_template.product_brand_id
                            """

            sql_query = "CREATE OR REPLACE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + where + groupby + " )"
            self._cr.execute(sql_query)

            # rule = """
            #         CREATE RULE quotation_product_list_UPDATE AS ON UPDATE TO quotation_product_list DO INSTEAD (
            #         UPDATE sale_order SET partner_id=partner_id WHERE id=id;
            #         UPDATE product_product SET id=id WHERE id=id;
            #         );
            # """
            # self._cr.execute(rule)

    @api.model_cr
    def delete_and_create(self):
        print('In delete and create')
        self.init_table()

    def update_record(self, product_id, partner_id, set_qty):
        print('In update_record')
        print(product_id)
        print(partner_id)
        print(set_qty)

        # result = self.env['quotation.product.list'].search([('product', '=', product_id)]).write({'quantity': set_qty})
        # print('record updated')
        # print(result)

        sql_query = """
                
                UPDATE quotation_product_list SET quantity=0 WHERE product = 10246
        """
        self._cr.execute(sql_query)
        print('records')
        records = self.env['quotation.product.list'].search([('partner', '=', partner_id)])
        print(records)
        for record in records:
            print(str(record.product.id) + "  " + str(record.quantity))

    # def get_saved_record(self):
    #     print('In get_saved_record')
    #     for ss in self:
    #         print(ss)