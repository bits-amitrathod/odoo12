from odoo import models, fields, api
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AvailableProductDict(models.TransientModel):
    _name = "available.product.dict"
    _description = "Available Product Dict"

    available_production_lot_dict_to_be_returned = {}
    available_production_lot_dict = {}

    # get available production lot list, parameter product id.
    def get_available_production_lot_dict(self, document_ids):
        self.available_production_lot_dict_to_be_returned.clear()

        sql_query = """Select sq.id, sq.product_id, sq.lot_id, sq.reserved_quantity, spl.use_date,  
                            sum(sq.quantity-sq.reserved_quantity) as available_qty from public.stock_quant sq 
                            Inner Join public.stock_location sl on sl.id = sq.location_id 
                            Inner Join public.stock_lot spl on sq.lot_id = spl.id 
                            where sq.product_id IN (Select distinct product_id 
                            from public.sps_customer_requests where document_id
                            """
        if len(document_ids) > 1:
            sql_query = sql_query + """  IN """ + str(document_ids)
        else:
            sql_query = sql_query + """ = """ + str(document_ids[0])

        sql_query = sql_query + """ ) and sq.quantity > 0 and spl.use_date is not null 
                        and sl.usage = 'internal' and sl.active = true and spl.use_date >= '""" + str(
            date.today()) + """'"""
        sql_query = sql_query + """ group by sq.id, spl.use_date, sq.product_id 
                        having sum(sq.quantity-sq.reserved_quantity) > 0 order by spl.use_date asc """

        self.env.cr.execute(sql_query)
        query_results = self.env.cr.dictfetchall()

        for query_result in query_results:
            if query_result['id'] and query_result['lot_id'] and query_result['product_id'] and query_result['use_date']:
                if query_result['available_qty'] > 0:
                    available_product = {query_result['lot_id']: {'stock_quant_id': query_result['id'],
                                                                  'available_quantity': query_result['available_qty'],
                                                                  'reserved_quantity': query_result['reserved_quantity'],
                                                                  'use_date': query_result['use_date'],
                                                                  'lot_id': query_result['lot_id']}}

                    if query_result['product_id'] in self.available_production_lot_dict_to_be_returned.keys():
                        self.available_production_lot_dict_to_be_returned.get(query_result['product_id'], {}).append(available_product)
                    else:
                        product_dict = {query_result['product_id']: [available_product]}
                        self.available_production_lot_dict_to_be_returned.update(product_dict)

        return self.available_production_lot_dict_to_be_returned

    def update_production_lot_dict(self):
        _logger.debug('In update db() %r', self.available_production_lot_dict_to_be_returned)

        for product_id_key in self.available_production_lot_dict_to_be_returned.keys():
            for available_production_lot in self.available_production_lot_dict_to_be_returned.get(product_id_key, {}):
                updated_dict = {'quantity': available_production_lot.get(list(available_production_lot.keys()).pop(0), {})['available_quantity'],
                                'reserved_quantity': available_production_lot.get(list(available_production_lot.keys()).pop(0), {})['reserved_quantity']}

                stock_quant = self.env['stock.quant'].search([('id', '=', available_production_lot.get(list(available_production_lot.keys()).pop(0), {})['stock_quant_id'])])
                stock_quant.write(dict(updated_dict))

    def get_available_production_lot(self, customer_id, product_id):
        self.available_production_lot_dict.clear()
        # get expiration tolerance
        prioritization_engine_request = self.env['sps.customer.requests'].get_settings_object(customer_id, product_id)
        expiration_tolerance_date = (date.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance'])))

        self.env.cr.execute("Select sq.id, sq.product_id, sq.lot_id, sq.reserved_quantity, spl.use_date, "
                            "sum(sq.quantity-sq.reserved_quantity) as available_qty from public.stock_quant sq "
                            "Inner Join public.stock_location sl on sl.id = sq.location_id "
                            "Inner Join public.stock_lot spl on sq.lot_id = spl.id "
                            "where sq.product_id = " + str(product_id) + " and sq.quantity > 0 "
                            "and spl.use_date is not null "
                            "and sl.usage = 'internal' and sl.active = true and spl.use_date >='"
                            + str(expiration_tolerance_date) + "' group by sq.id, spl.use_date "
                            "having sum(sq.quantity-sq.reserved_quantity) > 0 order by spl.use_date asc")

        query_results = self.env.cr.dictfetchall()

        for query_result in query_results:
            if query_result['id'] and query_result['lot_id'] and query_result['product_id'] and query_result['use_date']:
                if query_result['available_qty'] > 0:
                    available_product = {query_result['lot_id']: {'stock_quant_id': query_result['id'],
                                                                  'available_quantity': query_result['available_qty'],
                                                                  'reserved_quantity': query_result['reserved_quantity'],
                                                                  'use_date': query_result['use_date'],
                                                                  'lot_id': query_result['lot_id']}}

                    if query_result['product_id'] in self.available_production_lot_dict.keys():
                        self.available_production_lot_dict.get(query_result['product_id'], {}).append(available_product)
                    else:
                        product_dict = {query_result['product_id']: [available_product]}
                        self.available_production_lot_dict.update(product_dict)

        return self.available_production_lot_dict

    def get_available_product_qty(self, customer_id, product_id, expiration_tolerance):
        # get expiration tolerance date
        expiration_tolerance_date = (date.today() + relativedelta(months=+int(expiration_tolerance)))

        self.env.cr.execute("Select sum(sq.quantity-sq.reserved_quantity) as count from public.stock_quant sq "
                            "Inner Join public.stock_location sl on sl.id = sq.location_id "
                            "Inner Join public.stock_lot spl on sq.lot_id = spl.id "
                            "where sq.product_id = " + str(product_id) + " and sq.quantity > 0 "
                            "and spl.use_date is not null "                                             
                            "and sl.usage = 'internal' and sl.active = true and spl.use_date >='"
                            + str(expiration_tolerance_date) + "'")
        query_result = self.env.cr.dictfetchone()
        all_available_quantity = query_result['count']

        return all_available_quantity
