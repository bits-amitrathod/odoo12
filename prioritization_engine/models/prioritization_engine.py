from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime
import re

_logger = logging.getLogger(__name__)

class PrioritizationEngine(models.TransientModel):
    _inherit = 'crm.team'
    _name = 'prioritization.engine.model'

    team_type = fields.Selection([('prioritization', 'Prioritization')])

    allocated_product_dict = {}

    def allocate_product_by_priority(self, prioritization_engine_request_list):
        self.allocated_product_dict = {}
        _logger.debug('In product_allocation_by_priority')
        # get available production lot list.
        available_product_lot_dict = self.get_available_product_lot_dict()
        if len(available_product_lot_dict) > 0:
            for prioritization_engine_request in prioritization_engine_request_list:
                # auto allocate True/False
                if prioritization_engine_request['auto_allocate']:
                    prioritization_engine_request['customer_request_logs'] += 'Auto allocate is true, '
                    _logger.debug('Auto allocate is true....')
                    filter_available_product_lot_dict = self.filter_available_product_lot_dict(available_product_lot_dict, prioritization_engine_request)
                    if len(filter_available_product_lot_dict) >= 1:
                        # check cooling period- method return True/False
                        if self.check_cooling_period(prioritization_engine_request):
                            prioritization_engine_request['customer_request_logs'] += 'successed cooling period, '
                            _logger.debug('successed cooling period')
                            if prioritization_engine_request['template_type'].lower().strip() == 'inventory':
                                # check min-max threshold
                                _logger.debug('Template type is Inventory.')
                                flag, allocate_inventory_product_quantity = self.check_product_threshold(prioritization_engine_request)
                                if flag:
                                    #allocate product
                                    self.allocate_product(prioritization_engine_request, filter_available_product_lot_dict, allocate_inventory_product_quantity)
                            else:
                                # allocate product
                                self.allocate_product(prioritization_engine_request, filter_available_product_lot_dict, None)
                        else:
                            prioritization_engine_request['customer_request_logs'] += 'In Cooling period.'
                            _logger.debug('Cooling period false.....')
                    else:
                        prioritization_engine_request['customer_request_logs'] += 'Product Lot not available.'
                        _logger.debug('Product Lot not available....')
                else:
                    prioritization_engine_request['customer_request_logs'] += 'Auto allocate is false.'
                    _logger.debug('Auto allocate is false....')
                self.update_customer_request_logs(prioritization_engine_request)
            if len(self.allocated_product_dict) > 0:
                self.env['available.product.dict'].update_production_lot_dict()
                self.generate_sale_order()
        else:
            _logger.debug('Available product lot list is zero')
        return self.allocated_product_dict

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
    def check_cooling_period(self, prioritization_engine_request):
        flag = True
        if self.check_length_of_hold(prioritization_engine_request) :
            # get product create date
            create_date = self.get_product_create_date(prioritization_engine_request)
            if not create_date is None:
                # get current datetime
                current_datetime = datetime.now()
                create_date = datetime.strptime(self.change_date_format(create_date), '%Y,%m,%d,%H,%M,%S')
                #convert cooling period days into hours
                cooling_period_in_hours = int(prioritization_engine_request['cooling_period']) * 24;
                length_of_hold_in_hours = int(prioritization_engine_request['length_of_hold'])
                total_hours = cooling_period_in_hours + length_of_hold_in_hours
                # calculate datetime difference.
                duration = current_datetime - create_date  # For build-in functions
                duration_in_hours = self.return_duration_in_hours(duration)
                if int(total_hours) <= int(duration_in_hours):
                    if prioritization_engine_request['status'].lower().strip() != 'inprocess':
                        # update status In Process
                        self.update_customer_request_status(prioritization_engine_request, 'Inprocess')
                        flag = True
                elif prioritization_engine_request['status'].lower().strip() != 'incoolingperiod':
                        # update status In cooling period
                        self.update_customer_request_status(prioritization_engine_request, 'InCoolingPeriod')
                        flag = False
            else:
                flag = True
        else:
            # Product is in cooling period.
            flag = False
        return flag

    # calculate length of hold(In hours)
    def check_length_of_hold(self, prioritization_engine_request):
        flag = True
        # get previous sales order create date
        create_date = self.get_product_create_date(prioritization_engine_request)
        if not create_date is None:
            # get current datetime
            current_datetime = datetime.now()
            create_date = datetime.strptime(self.change_date_format(create_date), '%Y,%m,%d,%H,%M,%S')
            # calculate datetime difference.
            duration = current_datetime - create_date  # For build-in functions
            duration_in_hours = self.return_duration_in_hours(duration)
            if int(prioritization_engine_request['length_of_hold']) <= int(duration_in_hours):
                flag = True
            else:
                # update status In cooling period
                if prioritization_engine_request['status'].lower().strip() != 'incoolingperiod':
                    self.update_customer_request_status(prioritization_engine_request, 'InCoolingPeriod')
                    flag = False
        else:
            return flag

    # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    def get_product_expiration_tolerance_date(self,prioritization_engine_request):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance']))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, prioritization_engine_request, filter_available_product_lot_dict, allocate_inventory_product_quantity):
        remaining_product_allocation_quantity = 0
        if prioritization_engine_request['template_type'].lower().strip() == 'inventory':
            remaining_product_allocation_quantity = allocate_inventory_product_quantity
        else:
            remaining_product_allocation_quantity = prioritization_engine_request['required_quantity']
        for product_lot in filter_available_product_lot_dict.get(prioritization_engine_request['product_id'],{}):
            _logger.debug('**** %r',product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'))
            if remaining_product_allocation_quantity >= product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'):
                if prioritization_engine_request['partial_order']:
                    _logger.debug('product allocated from lot %r %r %r', product_lot.get(list(product_lot.keys()).pop(0), {}))

                    remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                    self.allocated_product_to_customer(prioritization_engine_request['customer_id'],
                                                       prioritization_engine_request['customer_request_id'],
                                                       prioritization_engine_request['required_quantity'],
                                                       list(product_lot.keys()).pop(0),
                                                       prioritization_engine_request['product_id'],
                                                       product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                    product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity'])
                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0

                    _logger.debug('Quantity Updated')
            elif remaining_product_allocation_quantity < product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'):
                    _logger.debug('product allocated from lot %r', list(product_lot.keys()).pop(0))

                    product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(remaining_product_allocation_quantity)
                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity']) - int(remaining_product_allocation_quantity)

                    self.allocated_product_to_customer(prioritization_engine_request['customer_id'], prioritization_engine_request['customer_request_id'], prioritization_engine_request['required_quantity'],
                                                       list(product_lot.keys()).pop(0), prioritization_engine_request['product_id'], remaining_product_allocation_quantity)

                    _logger.debug('Quantity Updated')

                    remaining_product_allocation_quantity = 0
                    break

        if prioritization_engine_request['template_type'].lower().strip() == 'inventory':
            if remaining_product_allocation_quantity == allocate_inventory_product_quantity:
                prioritization_engine_request['customer_request_logs'] += 'Partial ordering flag is False.'
                _logger.debug('Partial ordering flag is False')

        elif remaining_product_allocation_quantity == prioritization_engine_request['required_quantity']:
                prioritization_engine_request['customer_request_logs'] += 'Partial ordering flag is False.'
                _logger.debug('Partial ordering flag is False')

        if remaining_product_allocation_quantity == 0:
            _logger.debug("Allocated all required product quantity.")
            prioritization_engine_request['customer_request_logs'] += 'Product allocated.'
            self.update_customer_request_status(prioritization_engine_request,'Completed')

        elif remaining_product_allocation_quantity > 0:
            _logger.debug(str(" Allocated Partial order product."))
            prioritization_engine_request['customer_request_logs'] += 'Allocated Partial order product.'
            self.update_customer_request_status(prioritization_engine_request, 'Partial')

    # update customer status
    def update_customer_request_status(self,prioritization_engine_request,status):
        self.env['sps.customer.requests'].search(
            [('id', '=', prioritization_engine_request['customer_request_id'])]).write(dict(status=status))
        prioritization_engine_request['customer_request_logs'] += 'Updated customer request status.'

    def update_customer_request_logs(self, prioritization_engine_request):
        self.env['sps.customer.requests'].search(
            [('id', '=', prioritization_engine_request['customer_request_id'])]).write(dict(customer_request_logs=prioritization_engine_request['customer_request_logs']))

    # get product last purchased date, parameter product id
    def get_product_last_purchased_date(self, prioritization_engine_request):
        self.env.cr.execute(
            "SELECT max(saleorder.confirmation_date) as confirmation_date FROM public.sale_order_line saleorderline "
            " INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " WHERE saleorderline.order_partner_id = " + str(prioritization_engine_request['customer_id']) +
            " and saleorderline.product_id = " + str(prioritization_engine_request['product_id'])+
            " and saleorder.state = 'engine'")

        query_result = self.env.cr.dictfetchone()

        if query_result['confirmation_date'] != None:
            return query_result['confirmation_date']
        else:
            return None

    # get product create date for to calculate length of hold and cooling period.
    def get_product_create_date(self, prioritization_engine_request):
        self.env.cr.execute(
            "SELECT max(saleorder.create_date) as create_date FROM public.sale_order_line saleorderline "
            " INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " INNER JOIN public.crm_team crmteam ON crmteam.id = saleorder.team_id"
            " WHERE saleorderline.order_partner_id = " + str(prioritization_engine_request['customer_id']) +
            " and saleorderline.product_id = " + str(prioritization_engine_request['product_id']) +
            " and saleorder.state in ('engine','sent') and crmteam.team_type = 'engine'")
        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            _logger.debug('create date : %r', query_result['create_date'])
            return query_result['create_date']
        else:
            return None

    # allocated product to customer
    def allocated_product_to_customer(self, customer_id, customer_request_id, required_quantity, lot_id, product_id, allocated_product_from_lot):
        allocated_product = {lot_id : {'customer_request_id':customer_request_id, 'customer_required_quantity':required_quantity,
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
                sale_order_line_dict = {'customer_request_id': allocated_product.get(list(allocated_product.keys()).pop(0), {})['customer_request_id'], 'order_id': sale_order['id'], 'product_id': allocated_product.get(list(allocated_product.keys()).pop(0), {})['product_id'],
                                        'order_partner_id' : partner_id_key, 'product_uom_qty' : allocated_product.get(list(allocated_product.keys()).pop(0), {})['allocated_product_quantity']}

                self.env['sale.order.line'].create(dict(sale_order_line_dict))

    # Change date format to calculate date difference (2018-06-25 23:08:15) to (2018, 6, 25, 23, 8, 15)
    def change_date_format(self, date):
        formatted_date = date.split(".")[0].replace("-", ",").replace(" ", ",").replace(":", ",")
        return formatted_date

    def get_available_product_count(self, customer_id, product_id):
        available_production_lot_dict =self.env['available.product.dict'].get_available_production_lot()
        prioritization_engine_request=self.env['sps.customer.requests'].get_settings_object(customer_id,product_id,None,None)
        count = 0
        if available_production_lot_dict.get(int(product_id)) !=None and prioritization_engine_request:
            for available_production_lot in available_production_lot_dict.get(int(product_id)):
                temp=(datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance'])))
                if datetime.strptime(
                        available_production_lot.get(list(available_production_lot.keys()).pop(0), {}).get('use_date'),
                        '%Y-%m-%d %H:%M:%S') >= temp:
                    for available in available_production_lot:
                        print(available_production_lot.get(available))
                        count = count +(available_production_lot.get(available).get('available_quantity')-available_production_lot.get(available).get('reserved_quantity'))
        return count

    def check_product_threshold(self,prioritization_engine_request):
        if prioritization_engine_request['quantity'] < prioritization_engine_request['min_threshold']:
            allocate_quantity = prioritization_engine_request['max_threshold'] - prioritization_engine_request['quantity']
            return True,allocate_quantity
        else:
            return False,0



