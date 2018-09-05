from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime

_logger = logging.getLogger(__name__)

class PrioritizationEngine(models.TransientModel):

    _name = 'prioritization.engine.model'

    allocated_product_list = []

    def allocate_product_by_priority(self, prioritization_engine_request_list):
        _logger.info('In product_allocation_by_priority')
        # get available production lot list.
        available_product_lot_list = self.get_available_product_lot_list()
        if len(available_product_lot_list) > 0:
            for prioritization_engine_request in prioritization_engine_request_list:
                # auto allocate True/False
                if prioritization_engine_request['auto_allocate']:
                    _logger.info('Auto allocate is true....')
                    filter_available_product_lot_list = self.filter_available_product_lot_list(available_product_lot_list, prioritization_engine_request)
                    if len(filter_available_product_lot_list) >= 1:
                        # check cooling period- method return True/False
                        if self.calculate_cooling_priod_in_days(prioritization_engine_request):
                            _logger.info('successed cooling period')
                            # check length of holds- method return True/False
                            if self.calculate_length_of_holds_in_hours(prioritization_engine_request):
                                _logger.info('successed length of hold')
                                # allocate product
                                self.allocate_product(prioritization_engine_request, filter_available_product_lot_list)
                            else:
                                _logger.info('length of hold false....')
                        else:
                            _logger.info('Cooling period false.....')
                    else:
                        _logger.info('Product Lot not available....')
                else:
                    _logger.info('Auto allocate is false....')
            if len(self.allocated_product_list) > 0:
                #self.env['available.product.list'].update_production_lot_list()
                self.display_allocated_product_list()
        else:
            _logger.info('Available product lot list is zero')

    # get available production lot list, parameter product id.
    def get_available_product_lot_list(self):
        production_lot_list = self.env['available.product.list'].get_available_production_lot_list()
        _logger.info('Available production lot list : %r', production_lot_list)
        return production_lot_list

    def filter_available_product_lot_list(self, available_production_lot_list, prioritization_engine_request):
        filtered_production_lot_list_to_be_returned = []
        for available_production_lot in available_production_lot_list:
            if available_production_lot['product_id']['id'] == prioritization_engine_request['product_id']:
                if datetime.strptime(available_production_lot['use_date'],'%Y-%m-%d %H:%M:%S') >= self.get_product_expiration_tolerance_date(prioritization_engine_request):
                    filtered_production_lot_list_to_be_returned.append(available_production_lot)
        _logger.info('Filtered production lot list to be returned %r', str(filtered_production_lot_list_to_be_returned))
        return filtered_production_lot_list_to_be_returned

    # calculate cooling period
    def calculate_cooling_priod_in_days(self, prioritization_engine_request):
        # get product last purchased date
        confirmation_date = self.get_product_last_purchased_date(prioritization_engine_request)
        if not confirmation_date is None:
            # get current datetime
            current_datetime = datetime.datetime.now()
            # calculate datetime difference.
            duration = current_datetime - confirmation_date  # For build-in functions
            duration_in_days = self.return_duration_in_days(duration)
            _logger.info("duration_in_days is " + str(duration_in_days))
            if int(self.cooling_period) < int(duration_in_days):
                if prioritization_engine_request['status'].lower().strip() != 'inprocess':
                    # update status In Process
                    self.update_customer_status(prioritization_engine_request, 'Inprocess')
                    return True
            else:
                if prioritization_engine_request['status'].lower().strip() != 'incoolingperiod':
                    # update status In cooling period
                    self.update_customer_status(prioritization_engine_request, 'InCoolingPeriod')
                    return False
        else:
            return True

    # calculate length of hold(In hours)
    def calculate_length_of_holds_in_hours(self, prioritization_engine_request):
        # get product create date
        create_date = self.get_product_create_date(prioritization_engine_request)

        if not create_date is None:
            # get current datetime
            current_datetime = datetime.datetime.now()
            # calculate datetime difference.
            duration = current_datetime - create_date  # For build-in functions
            duration_in_hours = self.return_duration_in_hours(duration)
            _logger.info("duration_in_hours is " + str(duration_in_hours))
            if int(self.length_of_hold) < int(duration_in_hours):
                if prioritization_engine_request['status'].lower().strip() != 'inprocess':
                    # update status In Process
                    self.update_customer_status(prioritization_engine_request, 'Inprocess')
                    return True
            else:
                if prioritization_engine_request['status'].lower().strip() != 'unprocessed':
                    # update status In Process
                    self.update_customer_status(prioritization_engine_request, 'Unprocessed')
                    return False
        else:
            return True

    # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    def get_product_expiration_tolerance_date(self,prioritization_engine_request):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance']))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, prioritization_engine_request, filter_available_product_lot_list):
        remaining_product_allocation_quantity = prioritization_engine_request['required_quantity']
        for product_lot in filter_available_product_lot_list:
            if remaining_product_allocation_quantity >= product_lot['available_quantity']:
                if prioritization_engine_request['partial_order']:
                    _logger.info('product allocated from lot %r %r %r', product_lot['lot_id'])

                    remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot['available_quantity'])

                    product_lot['reserved_quantity'] = int(product_lot['reserved_quantity']) + int(product_lot['available_quantity'])
                    product_lot['available_quantity'] = 0

                    self.update_production_lot(product_lot['stock_quant_id'], product_lot['available_quantity'],
                                               product_lot['reserved_quantity'])

                    allocated_product = dict(customer_id=prioritization_engine_request['customer_id'],
                                             customer_required_quantity=prioritization_engine_request['required_quantity'],
                                             lot_id=product_lot['lot_id'],
                                             product_id=prioritization_engine_request['product_id'],
                                             allocated_product_from_lot=product_lot['available_quantity'])
                    self.allocated_product_list.append(allocated_product)

                _logger.info('Quantity Updated')
            else:
                if remaining_product_allocation_quantity < product_lot['available_quantity']:
                    _logger.info('product allocated from lot %r %r %r', product_lot['lot_id'])

                    product_lot['reserved_quantity'] = int(product_lot['reserved_quantity']) + int(remaining_product_allocation_quantity)
                    product_lot['available_quantity'] = int(product_lot['available_quantity']) - int(remaining_product_allocation_quantity)

                    self.update_production_lot(product_lot['stock_quant_id'], product_lot['available_quantity'],
                                               product_lot['reserved_quantity'])

                    allocated_product = dict(customer_id=prioritization_engine_request['customer_id'],
                                             customer_required_quantity=prioritization_engine_request['required_quantity'],
                                             lot_id=product_lot['lot_id'],
                                             product_id=prioritization_engine_request['product_id'],
                                             allocated_product_from_lot=remaining_product_allocation_quantity)
                    self.allocated_product_list.append(allocated_product)

                    _logger.info('Quantity Updated')

                    remaining_product_allocation_quantity = 0
                    break

        if remaining_product_allocation_quantity == prioritization_engine_request['required_quantity']:
            _logger.info('Partial ordering flag is False')

        elif remaining_product_allocation_quantity == 0:
            _logger.info("Allocated Partial order of product id " + str(
                prioritization_engine_request['product_id']) + ". Total required product quantity is " + str(
                prioritization_engine_request['required_quantity']))
            self.update_customer_status(prioritization_engine_request,'Completed')

        elif remaining_product_allocation_quantity > 0:
            allocated_product_quantity = int(prioritization_engine_request['required_quantity']) - int(
                remaining_product_allocation_quantity)
            _logger.info(str(" We have allocated only " + str(allocated_product_quantity) + " products. " + str(
                remaining_product_allocation_quantity) + " are pending."))
            self.update_customer_status(prioritization_engine_request, 'Partial')

    # update customer status
    def update_customer_status(self,prioritization_engine_request,status):
        self.env['sps.customer.requests'].search(
            [('id', '=', prioritization_engine_request['customer_request_id'])]).write(dict(status=status))

    # get product last purchased date, parameter product id
    def get_product_last_purchased_date(self, prioritization_engine_request):
        _logger.info("In get_product_last_purchased_date()")

        self.env.cr.execute(
            "SELECT max(order_id.confirmation_date) as confirmation_date FROM public.sale.order.line WHERE order_partner_id = " + str(
                prioritization_engine_request['customer_id']) +
            "and product_id = " + str(prioritization_engine_request['product_id']))

        query_result = self.env.cr.dictfetchone()

        if query_result['confirmation_date'] != None:
            return query_result['confirmation_date']
        else:
            return None

    # get product create date for to calculate length of hold, parameter product id
    def get_product_create_date(self, prioritization_engine_request):
        _logger.info("In get_product_create_date()")

        self.env.cr.execute(
            "SELECT max(order_id.create_date) as create_date FROM public.sale.order.line WHERE order_partner_id = " + str(
                prioritization_engine_request['customer_id']) +
            "and product_id = " + str(prioritization_engine_request['product_id']))
        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            return query_result['create_date']
        else:
            return None


    # return duration in days
    def return_duration_in_days(self, duration):
        duration_in_seconds = duration.total_seconds()
        duration_in_hours = duration_in_seconds / 3600
        duration_in_days = duration_in_hours / 24
        return duration_in_days

    # return duration in hours
    def return_duration_in_hours(self,duration):
        duration_in_seconds = duration.total_seconds()
        duration_in_hours = duration_in_seconds / 3600
        return duration_in_hours

    # display allocated product list
    def display_allocated_product_list(self):
        for allocated_product in self.allocated_product_list:
            _logger.info('In display allocated product list %r, %r, %r', str(allocated_product['customer_id']), str(allocated_product['product_id']), str(allocated_product['allocated_product_quantity']))
