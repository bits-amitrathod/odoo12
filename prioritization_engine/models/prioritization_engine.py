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
    allocated_product_for_gl_account_dict = {}

    def allocate_product_by_priority(self, prioritization_engine_request_list):
        self.allocated_product_dict = {}
        self.allocated_product_for_gl_account_dict = {}
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
                self.generate_sale_order()
            if len(self.allocated_product_for_gl_account_dict) > 0:
                self.generate_sale_order_for_gl_account()
            self.env['available.product.dict'].update_production_lot_dict()
            self._check_uploaded_document_status()
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
            flag = True
        return flag

    # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    def get_product_expiration_tolerance_date(self,prioritization_engine_request):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance']))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, prioritization_engine_request, filter_available_product_lot_dict, allocate_inventory_product_quantity):
        if prioritization_engine_request['template_type'].lower().strip() == 'inventory':
            required_quantity = allocate_inventory_product_quantity
            remaining_product_allocation_quantity = allocate_inventory_product_quantity
        else:
            required_quantity = prioritization_engine_request['required_quantity']
            remaining_product_allocation_quantity = prioritization_engine_request['required_quantity']
        for product_lot in filter_available_product_lot_dict.get(prioritization_engine_request['product_id'],{}):
            _logger.debug('**** %r',product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'))

            if int(remaining_product_allocation_quantity) > 0 and int(product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity')) > 0:
                if int(remaining_product_allocation_quantity) >= int(product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity')):
                    if prioritization_engine_request['partial_order']:
                        _logger.debug('product allocated from lot %r %r %r', product_lot.get(list(product_lot.keys()).pop(0), {}))

                        remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                        product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity'])
                        product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0

                        _logger.debug('Quantity Updated')
                elif int(remaining_product_allocation_quantity) < int(product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity')):
                        _logger.debug('product allocated from lot %r', list(product_lot.keys()).pop(0))

                        product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(remaining_product_allocation_quantity)
                        product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity']) - int(remaining_product_allocation_quantity)

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

            self.allocated_product_to_customer(prioritization_engine_request['customer_id'],
                                               prioritization_engine_request['gl_account'],
                                               prioritization_engine_request['customer_request_id'],
                                               prioritization_engine_request['required_quantity'],
                                               prioritization_engine_request['product_id'],
                                               required_quantity)

            prioritization_engine_request['customer_request_logs'] += 'Product allocated.'
            self.update_customer_request_status(prioritization_engine_request,'Completed')

        elif remaining_product_allocation_quantity > 0 and remaining_product_allocation_quantity != required_quantity:
            _logger.debug(str(" Allocated Partial order product."))

            self.allocated_product_to_customer(prioritization_engine_request['customer_id'],
                                               prioritization_engine_request['gl_account'],
                                               prioritization_engine_request['customer_request_id'],
                                               prioritization_engine_request['required_quantity'],
                                               prioritization_engine_request['product_id'],
                                               required_quantity - remaining_product_allocation_quantity)

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

    # get product create date for to calculate length of hold and cooling period.
    def get_product_create_date(self, prioritization_engine_request):
        self.env.cr.execute(
            "SELECT max(saleorder.create_date) as create_date FROM public.sale_order_line saleorderline "
            " INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " INNER JOIN public.crm_team crmteam ON crmteam.id = saleorder.team_id"
            " WHERE saleorderline.order_partner_id IN (SELECT distinct unnest(array[id, parent_id]) from public.res_partner WHERE parent_id = " +
            str(prioritization_engine_request['customer_id']) + ") " +
            " and saleorderline.product_id = " + str(prioritization_engine_request['product_id']) +
            " and saleorder.state in ('engine','sent') and crmteam.team_type = 'engine'")
        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            _logger.debug('create date : %r', query_result['create_date'])
            return query_result['create_date']
        else:
            return None

    # allocated product to customer
    def allocated_product_to_customer(self, customer_id, gl_account, customer_request_id, required_quantity, product_id, allocated_product_from_lot):
        allocated_product = {'customer_request_id':customer_request_id, 'customer_required_quantity':required_quantity,
                                 'product_id':product_id, 'allocated_product_quantity':allocated_product_from_lot}
        # add data in allocated_product_for_gl_account_dict
        if gl_account and not gl_account is None:
            # match parent id and gl account
            res_partner = self.env['res.partner'].search([('gl_account', '=', gl_account),('parent_id', '=', customer_id)])
            if res_partner:
                if len(res_partner) == 1:
                    if gl_account in self.allocated_product_for_gl_account_dict.keys():
                        self.allocated_product_for_gl_account_dict.get(gl_account, {}).append(allocated_product)
                    else:
                        new_gl_account_key = {gl_account: [allocated_product]}
                        self.allocated_product_for_gl_account_dict.update(new_gl_account_key)
                else:
                    _logger.info('same gl account for multiple customer')
            else:
                _logger.info('mismatch gl account for customer means customer id != parent id with gl account')
                if customer_id in self.allocated_product_dict.keys():
                    self.allocated_product_dict.get(customer_id, {}).append(allocated_product)
                else:
                    new_customer_id_key = {customer_id: [allocated_product]}
                    self.allocated_product_dict.update(new_customer_id_key)
        else:
            if customer_id in self.allocated_product_dict.keys():
                self.allocated_product_dict.get(customer_id, {}).append(allocated_product)
            else:
                new_customer_id_key = {customer_id: [allocated_product]}
                self.allocated_product_dict.update(new_customer_id_key)


    # return duration in days
    def return_duration_in_days(self, duration):
        duration_in_seconds = int(duration.total_seconds())
        duration_in_hours = duration_in_seconds / 3600
        duration_in_days = int(duration_in_hours) / 24
        return int(duration_in_days)

    # return duration in hours
    def return_duration_in_hours(self,duration):
        duration_in_seconds = int(duration.total_seconds())
        duration_in_hours = duration_in_seconds / 3600
        return int(duration_in_hours)

    # Generate sale order
    def generate_sale_order(self):
        _logger.debug('In generate sale order %r', self.allocated_product_dict)
        #get team id
        crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

        for partner_id_key in self.allocated_product_dict.keys():
            sale_order_dict = {'partner_id': partner_id_key, 'state': 'engine', 'team_id' : crm_team['id']}

            sale_order = self.env['sale.order'].create(dict(sale_order_dict))
            _logger.debug('sale order : %r ',sale_order['id'])

            for allocated_product in self.allocated_product_dict.get(partner_id_key, {}):
                _logger.info('customer_request_id  :**** ')
                _logger.info('customer_request_id  :  %r  ', allocated_product['customer_request_id'])

                sale_order_line_dict = {'customer_request_id': allocated_product['customer_request_id'], 'order_id': sale_order['id'], 'product_id': allocated_product['product_id'],
                                        'order_partner_id' : partner_id_key, 'product_uom_qty' : allocated_product['allocated_product_quantity']}

                self.env['sale.order.line'].create(dict(sale_order_line_dict))

            sale_order._action_confirm()
            sale_order.write(dict(state='engine', confirmation_date=''))


    # Generate sale order for gl account
    def generate_sale_order_for_gl_account(self):
        _logger.debug('In generate sale order for gl account %r', self.allocated_product_for_gl_account_dict)
        # get team id
        crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

        for gl_account_key in self.allocated_product_for_gl_account_dict.keys():
            _logger.debug('gl account key : %r', gl_account_key)
            # find partner id using gl account
            res_partner = self.env['res.partner'].search([('gl_account', '=', gl_account_key)])
            if res_partner:
                _logger.debug('res_partner : %r',res_partner.id)
                sale_order_dict = {'partner_id': res_partner.id, 'state': 'engine', 'team_id': crm_team['id']}

                sale_order = self.env['sale.order'].create(dict(sale_order_dict))
                _logger.debug('sale order : %r ', sale_order['id'])

                for allocated_product in self.allocated_product_for_gl_account_dict.get(gl_account_key, {}):
                    sale_order_line_dict = {
                        'customer_request_id': allocated_product['customer_request_id'], 'order_id': sale_order['id'],
                        'product_id': allocated_product['product_id'],'order_partner_id': res_partner.id,
                        'product_uom_qty': allocated_product['allocated_product_quantity']}

                    self.env['sale.order.line'].create(dict(sale_order_line_dict))

                sale_order._action_confirm()
                sale_order.write(dict(state='engine', confirmation_date=''))
            else:
                _logger.info('partner id is null')

    # Change date format to calculate date difference (2018-06-25 23:08:15) to (2018, 6, 25, 23, 8, 15)
    def change_date_format(self, date):
        formatted_date = date.split(".")[0].replace("-", ",").replace(" ", ",").replace(":", ",")
        return formatted_date

    def get_available_product_count(self, customer_id, product_id):
        _logger.info("inside get_available_product_count")
        available_production_lot_dict =self.env['available.product.dict'].get_available_production_lot()
        _logger.info(available_production_lot_dict)
        prioritization_engine_request=self.env['sps.customer.requests'].get_settings_object(int(customer_id),int(product_id),None,None)
        _logger.info(prioritization_engine_request)
        count = 0
        if available_production_lot_dict.get(int(product_id)) !=None and prioritization_engine_request:
            _logger.info("Inside IF block")
            for available_production_lot in available_production_lot_dict.get(int(product_id)):
                _logger.info(available_production_lot)
                _logger.info(prioritization_engine_request['expiration_tolerance'])
                temp=(datetime.today() + relativedelta(months=+int(prioritization_engine_request['expiration_tolerance'])))
                _logger.info(temp)
                if datetime.strptime(
                        available_production_lot.get(list(available_production_lot.keys()).pop(0), {}).get('use_date'),
                        '%Y-%m-%d %H:%M:%S') >= temp:
                    _logger.info("Inside IF2 block")
                    for available in available_production_lot:
                        _logger.info(available_production_lot.get(available))
                        count = count +(available_production_lot.get(available).get('available_quantity')-available_production_lot.get(available).get('reserved_quantity'))
        return count

    def check_product_threshold(self,prioritization_engine_request):
        if prioritization_engine_request['quantity'] < prioritization_engine_request['min_threshold']:
            allocate_quantity = prioritization_engine_request['max_threshold'] - prioritization_engine_request['quantity']
            return True,allocate_quantity
        else:
            return False,0

    # Update uploaded document status
    def _check_uploaded_document_status(self):
        # get all document whose status is draft and In Process.
        sps_cust_uploaded_documents = self.env['sps.cust.uploaded.documents'].search([('status', 'in', ('draft','In Process'))])

        for sps_cust_uploaded_document in sps_cust_uploaded_documents:
            _logger.info('Document Id :%r',sps_cust_uploaded_document.id)
            # get latest customer uploaded document id
            self.env.cr.execute("SELECT max(id) document_id FROM public.sps_cust_uploaded_documents WHERE customer_id=" +
                                    str(sps_cust_uploaded_document.customer_id.id))
            query_result = self.env.cr.dictfetchone()
            if sps_cust_uploaded_document.template_type.lower().strip() == 'requirement':
                if int(query_result['document_id']) == int(sps_cust_uploaded_document.id):
                    sps_customer_requirements = self.env['sps.customer.requests'].search(
                        [('document_id', '=', sps_cust_uploaded_document.id),
                         ('status', 'in', ('Partial', 'InCoolingPeriod', 'New', 'Inprocess', 'Incomplete', 'Unprocessed'))])
                    if len(sps_customer_requirements) > 0:
                        self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'In Process')
                    else:
                        self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')
                elif int(sps_cust_uploaded_document.document_processed_count) >=3:
                    self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')
                else:
                    self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'In Process')

            elif sps_cust_uploaded_document.template_type.lower().strip() == 'inventory':
                if int(query_result['document_id']) == int(sps_cust_uploaded_document.id):
                    sps_customer_requirements = self.env['sps.customer.requests'].search(
                        [('document_id', '=', sps_cust_uploaded_document.id),
                         ('status', 'in',
                          ('Partial', 'InCoolingPeriod', 'New', 'Inprocess', 'Incomplete', 'Unprocessed'))])
                    if len(sps_customer_requirements) > 0:
                        self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'In Process')
                    else:
                        self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')
                else:
                    self._update_uploaded_document_status(sps_cust_uploaded_document.id,'Completed')

    def _update_uploaded_document_status(self,document_id,status):
        self.env['sps.cust.uploaded.documents'].search(
            [('id', '=', document_id)]).write(dict(status=status))

    def release_reserved_quantity(self):
        _logger.debug('release reserved quantity....')
        # get team id
        crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

        sale_orders = self.env['sale.order'].search([('state', 'in', ('engine','sent')), ('team_id', '=', crm_team['id'])])

        for sale_order in sale_orders:
            _logger.debug('sale order id : %r, partner_id : %r, create_date: %r', sale_order['id'], sale_order['partner_id'].id, sale_order['create_date'])
            sale_order_lines = self.env['sale.order.line'].search([('order_id', '=', sale_order['id']), ('product_uom_qty', '>', 0)])

            for sale_order_line in sale_order_lines:
                _logger.debug('sale order line id : %r, product_id : %r, product_uom_qty: %r', sale_order_line['id'], sale_order_line['product_id'].id, sale_order_line['product_uom_qty'])

                # get length of hold
                _setting_object = self.env['sps.customer.requests'].get_settings_object(sale_order['partner_id'].id, sale_order_line['product_id'].id, None, None)
                _logger.debug('length of hold %r',_setting_object.length_of_hold)

                # get current datetime
                current_datetime = datetime.now()
                create_date = datetime.strptime(self.change_date_format(sale_order['create_date']), '%Y,%m,%d,%H,%M,%S')
                # calculate datetime difference.
                duration = current_datetime - create_date  # For build-in functions
                duration_in_hours = self.return_duration_in_hours(duration)
                if int(_setting_object.length_of_hold) <= int(duration_in_hours):
                    sale_order_line_dict = {'order_id': sale_order['id'], 'product_id': sale_order_line['product_id'].id, 'order_partner_id': sale_order['partner_id'].id, 'product_uom_qty': 0}

                    stock_move_lines = self.env['stock.move.line'].search([('picking_id.sale_id', '=', sale_order['id'])])

                    for stock_move_line in stock_move_lines:
                        _logger.debug('*Product_id  :  %r  ,picking_id  :  %r  ,product_uom_qty  : %r   ,  lot_id  :  %r ',stock_move_line['product_id'].id,
                                     stock_move_line['picking_id']['location_id']['id'], stock_move_line['product_uom_qty'], stock_move_line['lot_id']['id'])

                        self.env['stock.quant']._update_available_quantity(stock_move_line['product_id'], stock_move_line['picking_id']['location_id'],
                                                                              stock_move_line['product_uom_qty'],stock_move_line['lot_id'])

                        self.env['sale.order.line'].search([('customer_request_id', '=', sale_order_line['customer_request_id'].id)]).write(
                                                            dict(sale_order_line_dict))
                        stock_move_line.unlink()

                        _logger.info('Quantity Released')
                else:
                    _logger.info('Product is in length of hold, unable to release quantity.')










