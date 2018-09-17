from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime

_logger = logging.getLogger(__name__)

class PrioritizationEngine(models.TransientModel):
    _inherit = 'crm.team'
    _name = 'prioritization.engine.model'

    team_type = fields.Selection([('prioritization', 'Prioritization')])

    allocated_product_dict = {}

    def allocate_product_by_priority(self, prioritization_engine_request_list):
        _logger.debug('In product_allocation_by_priority')
        # get available production lot list.
        available_product_lot_dict = self.get_available_product_lot_dict()
        if len(available_product_lot_dict) > 0:
            for prioritization_engine_request in prioritization_engine_request_list:
                # auto allocate True/False
                if prioritization_engine_request['auto_allocate']:
                    prioritization_engine_request['customer_request_logs'] += 'Auto allocate is true....'
                    _logger.info('Auto allocate is true....')
                    filter_available_product_lot_dict = self.filter_available_product_lot_dict(available_product_lot_dict, prioritization_engine_request)
                    if len(filter_available_product_lot_dict) >= 1:
                        # check cooling period- method return True/False
                        if self.calculate_cooling_priod_in_days(prioritization_engine_request):
                            prioritization_engine_request['customer_request_logs'] += 'successed cooling period.....'
                            _logger.info('successed cooling period')
                            # check length of holds- method return True/False
                            if self.calculate_length_of_holds_in_hours(prioritization_engine_request):
                                prioritization_engine_request['customer_request_logs'] += 'successed length of hold....'
                                _logger.info('successed length of hold')
                                # allocate product
                                self.allocate_product(prioritization_engine_request, filter_available_product_lot_dict)
                            else:
                                prioritization_engine_request['customer_request_logs'] += 'length of hold false....'
                                _logger.info('length of hold false....')
                        else:
                            prioritization_engine_request['customer_request_logs'] += 'Cooling period false.....'
                            _logger.info('Cooling period false.....')
                    else:
                        prioritization_engine_request['customer_request_logs'] += 'Product Lot not available....'
                        _logger.info('Product Lot not available....')
                else:
                    prioritization_engine_request['customer_request_logs'] += 'Auto allocate is false....'
                    _logger.info('Auto allocate is false....')
                self.update_customer_request_logs(prioritization_engine_request)
            if len(self.allocated_product_dict) > 0:
                self.env['available.product.dict'].update_production_lot_dict()
                self.generate_sale_order()
        else:
            _logger.info('Available product lot list is zero')

    # get available production lot list, parameter product id.
    def get_available_product_lot_dict(self):
        production_lot_dict = self.env['available.product.dict'].get_available_production_lot_dict()
        return production_lot_dict

    def filter_available_product_lot_dict(self, available_production_lot_dict, prioritization_engine_request):
        filtered_production_lot_dict_to_be_returned = {}
        for available_production_lot in available_production_lot_dict.get(prioritization_engine_request['product_id'],{}):
            if datetime.strptime(available_production_lot.get(list(available_production_lot.keys()).pop(0), {}).get('use_date'),
                    '%Y-%m-%d %H:%M:%S') >= self.get_product_expiration_tolerance_date(prioritization_engine_request):

                if prioritization_engine_request['product_id'] in filtered_production_lot_dict_to_be_returned.keys():
                    filtered_production_lot_dict_to_be_returned.get(prioritization_engine_request['product_id'],
                                                                         {}).append(available_production_lot)
                else:
                    dict = {prioritization_engine_request['product_id']: [available_production_lot]}
                    filtered_production_lot_dict_to_be_returned.update(dict)

        _logger.debug('Filtered production lot list to be returned %r', str(filtered_production_lot_dict_to_be_returned))
        return filtered_production_lot_dict_to_be_returned

    # calculate cooling period
    def calculate_cooling_priod_in_days(self, prioritization_engine_request):
        flag = True
        # get product last purchased date
        confirmation_date = self.get_product_last_purchased_date(prioritization_engine_request)
        if not confirmation_date is None:
            # get current datetime
            current_datetime = datetime.now()
            confirmation_date = datetime.strptime(self.change_date_format(confirmation_date), '%Y,%m,%d,%H,%M,%S')
            # calculate datetime difference.
            duration = current_datetime - confirmation_date  # For build-in functions
            duration_in_days = self.return_duration_in_days(duration)
            if int(prioritization_engine_request['cooling_period']) <= int(duration_in_days):
                if prioritization_engine_request['status'].lower().strip() != 'inprocess':
                    # update status In Process
                    self.update_customer_status(prioritization_engine_request, 'Inprocess')
                    flag = True
            elif prioritization_engine_request['status'].lower().strip() != 'incoolingperiod':
                    # update status In cooling period
                    self.update_customer_status(prioritization_engine_request, 'InCoolingPeriod')
                    flag = False
        else:
            flag = True
        return flag

    # calculate length of hold(In hours)
    def calculate_length_of_holds_in_hours(self, prioritization_engine_request):
        flag = True
        # get product create date
        create_date = self.get_product_create_date(prioritization_engine_request)

        if not create_date is None:
            # get current datetime
            current_datetime = datetime.now()
            create_date = datetime.strptime(self.change_date_format(create_date), '%Y,%m,%d,%H,%M,%S.%f')
            # calculate datetime difference.
            duration = current_datetime - create_date  # For build-in functions
            duration_in_hours = self.return_duration_in_hours(duration)
            if int(prioritization_engine_request['length_of_hold']) <= int(duration_in_hours):
                if prioritization_engine_request['status'].lower().strip() != 'inprocess':
                    # update status In Process
                    self.update_customer_status(prioritization_engine_request, 'Inprocess')
                    flag = True
            elif prioritization_engine_request['status'].lower().strip() != 'unprocessed':
                    # update status In Process
                    self.update_customer_status(prioritization_engine_request, 'Unprocessed')
                    flag = False
        else:
            flag = True
        return flag


        # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    def get_product_expiration_tolerance_date(self,prioritization_engine_request):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance']))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, prioritization_engine_request, filter_available_product_lot_dict):
        remaining_product_allocation_quantity = prioritization_engine_request['required_quantity']
        for product_lot in filter_available_product_lot_dict.get(prioritization_engine_request['product_id'],{}):
            _logger.debug('**** %r',product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'))
            if remaining_product_allocation_quantity >= product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'):
                if prioritization_engine_request['partial_order']:
                    _logger.debug('product allocated from lot %r %r %r', product_lot.get(list(product_lot.keys()).pop(0), {}))

                    remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                    self.allocated_product_to_customer(prioritization_engine_request['customer_id'],
                                                       prioritization_engine_request['required_quantity'],
                                                       list(product_lot.keys()).pop(0),
                                                       prioritization_engine_request['product_id'],
                                                       product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                    product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity'])
                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0

                    _logger.debug('Quantity Updated')
            elif remaining_product_allocation_quantity < product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'):
                    _logger.info('product allocated from lot %r', list(product_lot.keys()).pop(0))

                    product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(remaining_product_allocation_quantity)
                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity']) - int(remaining_product_allocation_quantity)

                    self.allocated_product_to_customer(prioritization_engine_request['customer_id'], prioritization_engine_request['required_quantity'],
                                                       list(product_lot.keys()).pop(0), prioritization_engine_request['product_id'], remaining_product_allocation_quantity)

                    _logger.debug('Quantity Updated')

                    remaining_product_allocation_quantity = 0
                    break

        if remaining_product_allocation_quantity == prioritization_engine_request['required_quantity']:
            _logger.info('Partial ordering flag is False')

        elif remaining_product_allocation_quantity == 0:
            _logger.debug("Allocated product id " + str(
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

    def update_customer_request_logs(self, prioritization_engine_request):
        self.env['sps.customer.requests'].search(
            [('id', '=', prioritization_engine_request['customer_request_id'])]).write(dict(customer_request_logs=prioritization_engine_request['customer_request_logs']))

    # get product last purchased date, parameter product id
    def get_product_last_purchased_date(self, prioritization_engine_request):
        _logger.debug("In get_product_last_purchased_date()")

        self.env.cr.execute(
            "SELECT max(saleorder.confirmation_date) as confirmation_date FROM public.sale_order_line saleorderline "
            "INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            "WHERE saleorderline.order_partner_id = " + str(prioritization_engine_request['customer_id']) +
            " and saleorderline.product_id = " + str(prioritization_engine_request['product_id']))

        query_result = self.env.cr.dictfetchone()

        if query_result['confirmation_date'] != None:
            return query_result['confirmation_date']
        else:
            return None

    # get product create date for to calculate length of hold, parameter product id
    def get_product_create_date(self, prioritization_engine_request):
        _logger.debug("In get_product_create_date()")

        self.env.cr.execute(
            "SELECT max(saleorder.create_date) as create_date FROM public.sale_order_line saleorderline "
            "INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " WHERE saleorderline.order_partner_id = " + str(prioritization_engine_request['customer_id']) +
            " and saleorderline.product_id = " + str(prioritization_engine_request['product_id']))
        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            return query_result['create_date']
        else:
            return None

    # allocated product to customer
    def allocated_product_to_customer(self, customer_id, required_quantity, lot_id, product_id, allocated_product_from_lot):
        allocated_product = {lot_id : {'customer_required_quantity':required_quantity,
                                 'product_id':product_id, 'allocated_product_quantity':allocated_product_from_lot}}
        if customer_id in self.allocated_product_dict.keys():
            self.allocated_product_dict.get(customer_id, {}).append(allocated_product)
        else:
            dict = {customer_id: [allocated_product]}
            self.allocated_product_dict.update(dict)


    # return duration in days
    def return_duration_in_days(self, duration):
        duration_in_seconds = duration.total_seconds()
        duration_in_hours = duration_in_seconds / 3600
        duration_in_days = int(duration_in_hours) / 24
        return int(duration_in_days)

    # return duration in hours
    def return_duration_in_hours(self,duration):
        duration_in_seconds = duration.total_seconds()
        duration_in_hours = duration_in_seconds / 3600
        return int(duration_in_hours)

    # display allocated product list
    def generate_sale_order(self):
        _logger.debug('In generate sale order %r', self.allocated_product_dict)
        #get team id
        crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

        for partner_id_key in self.allocated_product_dict.keys():
            sale_order_dict = {'partner_id': partner_id_key, 'state': 'engine', 'team_id' : crm_team['id']}

            sale_order = self.env['sale.order'].create(dict(sale_order_dict))
            _logger.debug('sale order : %r ',sale_order['id'])

            for allocated_product in self.allocated_product_dict.get(partner_id_key, {}):
                sale_order_line_dict = {'order_id': sale_order['id'], 'product_id': allocated_product.get(list(allocated_product.keys()).pop(0), {})['product_id'],
                                        'order_partner_id' : partner_id_key, 'product_uom_qty' : allocated_product.get(list(allocated_product.keys()).pop(0), {})['allocated_product_quantity']}

                self.env['sale.order.line'].create(dict(sale_order_line_dict))

    # Change date format to calculate date difference (2018-06-25 23:08:15) to (2018, 6, 25, 23, 8, 15)
    def change_date_format(self, date):
        formatted_date = date.replace("-", ",").replace(" ", ",").replace(":", ",")
        return formatted_date
