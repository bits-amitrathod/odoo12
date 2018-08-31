from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime

_logger = logging.getLogger(__name__)
allocated_product_list = []


class PrioritizationEngine(models.TransientModel):

    _name = 'prioritization.engine.model'

    def allocate_product_by_priority(self, prioritization_engine_request_list):
        _logger.info('In product_allocation_by_priority')
        for prioritization_engine_request in prioritization_engine_request_list:
            # auto allocate True/False
            if prioritization_engine_request['auto_allocate']:
                # get available production lot list.
                product_lot_list = self.get_available_product_lot_list(prioritization_engine_request)
                if len(product_lot_list) >= 1:
                    # check cooling period- method return True/False
                    if self.calculate_cooling_priod_in_days(prioritization_engine_request):
                        _logger.info('successed cooling period')
                        # check length of holds- method return True/False
                        if self.calculate_length_of_holds_in_hours(prioritization_engine_request):
                            _logger.info('successed length of hold')
                            # allocate product
                            if self.allocate_product(prioritization_engine_request, product_lot_list):
                                _logger.info('product allocated....')
                            # check partial order flag is True or False
                            elif prioritization_engine_request['partial_order']:
                                _logger.info('Partial ordering flag is True')
                                self.allocate_partial_order_product(prioritization_engine_request, product_lot_list)
                            else:
                                _logger.info('Partial ordering flag is False')
                        else:
                            _logger.info('In length of hold false....')
                    else:
                        _logger.info('In cooling period false.....')
                else:
                    _logger.info('Product Lot not available....')
            else:
                _logger.info('Auto allocate is false....')

        self.env['available.product.list'].update_production_lot_list()
        self.env['allocated.product.list'].display_allocated_product_list()

    # get available production lot list, parameter product id.
    def get_available_product_lot_list(self,prioritization_engine_request):
        production_lot_list = self.env['available.product.list'].get_available_production_lot_list()
        _logger.info('production_lot_list ^^^^^: %r', production_lot_list)
        filtered_production_lot_list_to_be_returned = []

        for production_lot in production_lot_list:
            if datetime.strptime(production_lot.use_date,
                                     '%Y-%m-%d %H:%M:%S') >= self.get_product_expiration_tolerance_date(prioritization_engine_request):
                filtered_production_lot_list_to_be_returned.append(production_lot)
        _logger.info('filtered_production_lot_list_to_be_returned %r', filtered_production_lot_list_to_be_returned)
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
            duration_in_seconds = duration.total_seconds()  # Total number of seconds between dates
            duration_in_hours = duration_in_seconds / 3600  # Total number of hours between dates
            duration_in_days = duration_in_hours / 24
            _logger.info("duration_in_days is " + str(duration_in_days))
            if int(self.cooling_period) < int(duration_in_days):
                return True
            else:
                # update status In cooling period
                self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write(dict(status='InCoolingPeriod'))
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
            duration_in_seconds = duration.total_seconds()  # Total number of seconds between dates
            duration_in_hours = duration_in_seconds / 3600  # Total number of hours between dates
            _logger.info("duration_in_hours is " + str(duration_in_hours))
            if int(self.length_of_hold) < int(duration_in_hours):
                return True
            else:
                # update status In Process
                self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write(dict(status='Unprocessed'))
                return False
        else:
            return True

    # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    def get_product_expiration_tolerance_date(self,prioritization_engine_request):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance']))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, prioritization_engine_request, product_lot_list):
        product_allocation_flag = False
        for product_lot in product_lot_list:
            if product_lot.available_quantity >= prioritization_engine_request['required_quantity']:
                _logger.info('product allocated from lot %r %r %r %r', product_lot.lot_id, product_lot.available_quantity,product_lot.available_quantity,
                             prioritization_engine_request['required_quantity'])

                product_lot.reserved_quantity = int(product_lot.reserved_quantity) + int(prioritization_engine_request['required_quantity'])
                product_lot.available_quantity = int(product_lot.available_quantity) - int(prioritization_engine_request['required_quantity'])

                self.env['allocated.product.list'].add_allocated_products(prioritization_engine_request['customer_id'],prioritization_engine_request['product_id'],prioritization_engine_request['required_quantity'])
                # allocated_product_list.append(allocated_product)
                self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write(
                    dict(status='Completed'))

                product_allocation_flag = True
                break
        return product_allocation_flag


    # Allocate partial order product
    def allocate_partial_order_product(self, prioritization_engine_request, product_lot_list):
        remaining_product_allocation_quantity = prioritization_engine_request['required_quantity']
        for product_lot in product_lot_list:
            if remaining_product_allocation_quantity >= product_lot.available_quantity:
                _logger.info('product allocated from lot %r %r %r', product_lot.lot_id)

                remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot.available_quantity)

                product_lot.reserved_quantity = int(product_lot.reserved_quantity) + int(product_lot.available_quantity)
                product_lot.available_quantity = 0

                _logger.info('Quantity Updated')
            else:
                if remaining_product_allocation_quantity < product_lot.available_quantity:
                    _logger.info('product allocated from lot %r %r %r', product_lot.lot_id)

                    product_lot.reserved_quantity = int(product_lot.reserved_quantity) + int(remaining_product_allocation_quantity)
                    product_lot.available_quantity = int(product_lot.available_quantity) - int(remaining_product_allocation_quantity)

                    _logger.info('Quantity Updated')

                    remaining_product_allocation_quantity = 0

        if remaining_product_allocation_quantity == 0:
            _logger.info("Allocated Partial order of product id " + str(
                prioritization_engine_request['product_id']) + ". Total required product quantity is " + str(
                prioritization_engine_request['required_quantity']))

            allocated_product = self.env['allocated.product.list'].add_allocated_products(
                prioritization_engine_request['customer_id'], prioritization_engine_request['product_id'],
                prioritization_engine_request['required_quantity'])
            allocated_product_list.append(allocated_product)

            self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write(
                    dict(status='Completed'))
        elif remaining_product_allocation_quantity > 0:
            allocated_product_quantity = int(prioritization_engine_request['required_quantity']) - int(
                remaining_product_allocation_quantity)
            _logger.info(str(" We have allocated only " + str(allocated_product_quantity) + " products. " + str(
                remaining_product_allocation_quantity) + " are pending."))

            allocated_product = self.pool.get('allocated.product.list')
            allocated_product.add_allocated_products(
                prioritization_engine_request['customer_id'], prioritization_engine_request['product_id'],
                allocated_product_quantity)
            allocated_product_list.append(allocated_product)

            self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write(
                    dict(status='Partial'))

    # get product last purchased date, parameter product id
    def get_product_last_purchased_date(self, prioritization_engine_request):
        _logger.info("In get_product_last_purchased_date()")
        sale_orders_line = self.env['sale.order.line'].search([('product_id', '=', prioritization_engine_request['product_id'])])
        sorted_sale_orders_line = sorted([line for line in sale_orders_line if line.order_id.confirmation_date],
                                         key=self._sort_by_confirmation_date, reverse=True)
        if len(sorted_sale_orders_line)> 0:
            sorted_sale_orders_line.pop(1)  # get only first record
            _logger.info("^^^^" + str(sorted_sale_orders_line.order_id) + str(
                sorted_sale_orders_line.order_id.confirmation_date) + str(sorted_sale_orders_line.product_id.id))
            return sorted_sale_orders_line.order_id.confirmation_date
        else:
            return None


    @staticmethod
    def _sort_by_confirmation_date(sale_order_dict):
        if sale_order_dict.order_id.confirmation_date:
            return datetime.strptime(sale_order_dict.order_id.confirmation_date, '%Y-%m-%d %H:%M:%S')

    # get product create date for to calculate length of hold, parameter product id
    def get_product_create_date(self, prioritization_engine_request):
        _logger.info("In get_product_create_date()")
        sale_orders_line = self.env['sale.order.line'].search([('product_id', '=', prioritization_engine_request['product_id'])])

        sorted_sale_orders_line = sorted([line for line in sale_orders_line if line.order_id.create_date], key=self._sort_by_create_date, reverse=True)

        if len(sorted_sale_orders_line) > 1:
            sorted_sale_orders_line.pop(1) #get only first record
            _logger.info("^^^^"+ str(sorted_sale_orders_line.order_id) + str(sorted_sale_orders_line.order_id.create_date) + str(sorted_sale_orders_line.product_id))
            return sorted_sale_orders_line.order_id.create_date
        else:
            return None


    @staticmethod
    def _sort_by_create_date(sale_order_dict):
        if sale_order_dict.order_id.create_date:
            return datetime.strptime(sale_order_dict.order_id.create_date, '%Y-%m-%d %H:%M:%S')

    # Change date format to calculate date difference (2018-06-25 23:08:15) to (2018, 6, 25, 23, 8, 15)
    def change_date_format(self, date):
        formatted_date = date.replace("-", ",").replace(" ", ",").replace(":", ",")
        return formatted_date
