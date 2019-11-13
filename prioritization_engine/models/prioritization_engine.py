from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime
import re
from odoo import SUPERUSER_ID

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
                    filter_available_product_lot_dict = self.filter_available_product_lot_dict(available_product_lot_dict, prioritization_engine_request['product_id'],prioritization_engine_request['expiration_tolerance'])
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
                        prioritization_engine_request['customer_request_logs'] += 'As per requested expiration tolerance product lot not available.'
                        _logger.debug('As per requested expiration tolerance product lot not available.')
                else:
                    prioritization_engine_request['customer_request_logs'] += 'Auto allocate is false.'
                    _logger.debug('Auto allocate is false....')
                self.update_customer_request_logs(prioritization_engine_request)
            if len(self.allocated_product_dict) > 0:
                self.generate_sale_order()
            if len(self.allocated_product_for_gl_account_dict) > 0:
                self.generate_sale_order_for_gl_account()
            # self.env['available.product.dict'].update_production_lot_dict()
            self._check_uploaded_document_status()
        else:
            _logger.debug('Available product lot list is zero')
        return self.allocated_product_dict

    # get available production lot list, parameter product id.
    def get_available_product_lot_dict(self):
        production_lot_dict = self.env['available.product.dict'].get_available_production_lot_dict()
        return production_lot_dict

    def filter_available_product_lot_dict(self, available_production_lot_dict, product_id, expiration_tolerance):
        filtered_production_lot_dict_to_be_returned = {}
        filtered_production_lot_dict_to_be_returned.clear()
        for available_production_lot in available_production_lot_dict.get(product_id,{}):
            if datetime.strptime(str(available_production_lot.get(list(available_production_lot.keys()).pop(0), {}).get('use_date')),
                    '%Y-%m-%d %H:%M:%S') >= self.get_product_expiration_tolerance_date(expiration_tolerance):

                if product_id in filtered_production_lot_dict_to_be_returned.keys():
                    filtered_production_lot_dict_to_be_returned.get(product_id,{}).append(available_production_lot)
                else:
                    dict = {product_id: [available_production_lot]}
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
                cooling_period_in_hours = int(prioritization_engine_request['cooling_period']) * 24
                length_of_hold_in_hours = int(prioritization_engine_request['length_of_hold'])
                total_hours = cooling_period_in_hours + length_of_hold_in_hours
                # calculate datetime difference.
                duration = current_datetime - create_date  # For build-in functions
                duration_in_hours = self.return_duration_in_hours(duration)
                if int(total_hours) <= int(duration_in_hours):
                    _logger.info('True')
                    if prioritization_engine_request['status'].lower().strip() != 'inprocess':
                        # update status In Process
                        self.update_customer_request_status(prioritization_engine_request, 'Inprocess')
                    flag = True
                else:
                    if prioritization_engine_request['status'].lower().strip() != 'incoolingperiod' and prioritization_engine_request['status'].lower().strip() != 'partial':
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
                if prioritization_engine_request['status'].lower().strip() != 'incoolingperiod' and prioritization_engine_request['status'].lower().strip() != 'partial':
                    self.update_customer_request_status(prioritization_engine_request, 'InCoolingPeriod')
                flag = False
        else:
            flag = True
        return flag

    # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    def get_product_expiration_tolerance_date(self,expiration_tolerance):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(expiration_tolerance))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, prioritization_engine_request, filter_available_product_lot_dict, allocate_inventory_product_quantity):
        if prioritization_engine_request['template_type'].lower().strip() == 'inventory':
            required_quantity = allocate_inventory_product_quantity
            remaining_product_allocation_quantity = allocate_inventory_product_quantity
        else:
            required_quantity = prioritization_engine_request['updated_quantity']
            remaining_product_allocation_quantity = prioritization_engine_request['updated_quantity']
        for product_lot in filter_available_product_lot_dict.get(prioritization_engine_request['product_id'],{}):
            _logger.debug('**** %r',product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity'))

            if int(remaining_product_allocation_quantity) > 0 and int(product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity')) > 0:
                if int(remaining_product_allocation_quantity) > int(product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity')):
                    if prioritization_engine_request['partial_order']:
                        if prioritization_engine_request['uom_flag']:
                            _logger.debug('product allocated from lot %r %r %r', product_lot.get(list(product_lot.keys()).pop(0), {}))

                            remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                            product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity'])
                            product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0
                        else:
                            if prioritization_engine_request['partial_uom']:
                                remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0
                            else:
                                allocate_qty_by_partial_uom = self._get_quantity_by_partial_uom(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'], prioritization_engine_request)

                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(allocate_qty_by_partial_uom)
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(allocate_qty_by_partial_uom)

                                remaining_product_allocation_quantity = remaining_product_allocation_quantity - allocate_qty_by_partial_uom

                elif int(remaining_product_allocation_quantity) <= int(product_lot.get(list(product_lot.keys()).pop(0),{}).get('available_quantity')):
                        _logger.debug('product allocated from lot %r', list(product_lot.keys()).pop(0))

                        if prioritization_engine_request['uom_flag']:
                            product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['reserved_quantity']) + int(remaining_product_allocation_quantity)
                            product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0),{})['available_quantity']) - int(remaining_product_allocation_quantity)

                            remaining_product_allocation_quantity = 0
                            break
                        else:
                            if prioritization_engine_request['partial_uom']:
                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(remaining_product_allocation_quantity)
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(remaining_product_allocation_quantity)

                                remaining_product_allocation_quantity = 0
                                break
                            else:
                                allocate_qty_by_partial_uom = self._get_quantity_by_partial_uom(remaining_product_allocation_quantity, prioritization_engine_request)

                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(allocate_qty_by_partial_uom)
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(allocate_qty_by_partial_uom)

                                remaining_product_allocation_quantity = remaining_product_allocation_quantity - allocate_qty_by_partial_uom
                                break

        if prioritization_engine_request['template_type'].lower().strip() == 'inventory':
            if remaining_product_allocation_quantity == allocate_inventory_product_quantity:
                self._update_logs(prioritization_engine_request)
        elif remaining_product_allocation_quantity == prioritization_engine_request['updated_quantity']:
            self._update_logs(prioritization_engine_request)

        if remaining_product_allocation_quantity == 0:
            _logger.debug("Allocated all required product quantity.")

            self.allocated_product_to_customer(prioritization_engine_request['customer_id'],
                                               prioritization_engine_request['req_no'],
                                               prioritization_engine_request['gl_account'],
                                               prioritization_engine_request['customer_request_id'],
                                               required_quantity,
                                               prioritization_engine_request['product_id'],
                                               required_quantity)

            prioritization_engine_request['customer_request_logs'] += 'Product allocated.'
            self.update_customer_request_status(prioritization_engine_request,'Fulfilled')

            # Update updated_quantity
            if prioritization_engine_request['template_type'].lower().strip() == 'requirement':
                self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write({'updated_quantity': remaining_product_allocation_quantity})

        elif remaining_product_allocation_quantity > 0 and remaining_product_allocation_quantity != required_quantity:
            _logger.debug(str(" Allocated Partial order product."))


            self.allocated_product_to_customer(prioritization_engine_request['customer_id'],
                                               prioritization_engine_request['req_no'],
                                               prioritization_engine_request['gl_account'],
                                               prioritization_engine_request['customer_request_id'],
                                               required_quantity,
                                               prioritization_engine_request['product_id'],
                                               required_quantity - remaining_product_allocation_quantity)

            self._update_logs(prioritization_engine_request)
            prioritization_engine_request['customer_request_logs'] += ' Allocated Partial order product.'
            self.update_customer_request_status(prioritization_engine_request, 'Partial')

            # Update updated_quantity
            if prioritization_engine_request['template_type'].lower().strip() == 'requirement':
                self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write({'updated_quantity':remaining_product_allocation_quantity})

    # Update Prioritization Engine logs.
    def _update_logs(self, prioritization_engine_request):
        if prioritization_engine_request['partial_order']:
            prioritization_engine_request['customer_request_logs'] += 'Partial ordering flag is True.'
            _logger.debug('Partial ordering flag is True')
            if prioritization_engine_request['partial_uom']:
                prioritization_engine_request['customer_request_logs'] += 'Partial UOM flag is True.'
                _logger.debug('Partial UOM is True')
            else:
                prioritization_engine_request['customer_request_logs'] += 'Partial UOM flag is False.'
                _logger.debug('Partial UOM is False')
        else:
            prioritization_engine_request['customer_request_logs'] += 'Partial ordering flag is False.'
            _logger.debug('Partial ordering flag is False')


    #get quantitty by partial uom flag
    def _get_quantity_by_partial_uom(self, quantity, prioritization_engine_request):
        product = self.env['product.template'].search([('id', '=', prioritization_engine_request['product_id'])])
        uom = self.env['uom.uom'].search([('name', 'ilike', 'Unit'),('category_id.id', '=', 1)])
        if len(uom) == 0:
            uom = self.env['uom.uom'].search([('name', 'ilike', 'Each'),('category_id.id', '=', 1)])
        if product.manufacturer_uom.uom_type == 'bigger':
            uom_factor = product.manufacturer_uom.factor_inv
        elif product.manufacturer_uom.uom_type == 'smaller':
            uom_factor = product.manufacturer_uom.factor
        else:
            uom_factor = 1

        ratio = int(quantity / uom_factor)
        allocate_qty_by_partial_uom = int(product.manufacturer_uom._compute_quantity(float(ratio), uom))
        return allocate_qty_by_partial_uom

    # update customer status
    def update_customer_request_status(self,prioritization_engine_request,status):
        self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write({'status':status})
        # prioritization_engine_request['customer_request_logs'] += 'Updated customer request status.'

    def update_customer_request_logs(self, prioritization_engine_request):
        self.env['sps.customer.requests'].search([('id', '=', prioritization_engine_request['customer_request_id'])]).write({'customer_request_logs':prioritization_engine_request['customer_request_logs']})

    # get product create date for to calculate length of hold and cooling period.
    def get_product_create_date(self, prioritization_engine_request):
        self.env.cr.execute(
            "SELECT max(saleorder.create_date) as create_date FROM public.sale_order_line saleorderline "
            " INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " INNER JOIN public.crm_team crmteam ON crmteam.id = saleorder.team_id"
            " WHERE saleorderline.order_partner_id IN (SELECT distinct unnest(array[id, parent_id]) from public.res_partner WHERE parent_id = " +
            str(prioritization_engine_request['customer_id']) + " or id = " + str(prioritization_engine_request['customer_id']) + " ) " +
            " and saleorderline.product_id = " + str(prioritization_engine_request['product_id']) +
            " and ((saleorder.state in ('engine','sent','cancel')) or (saleorder.state in ('sent','sale') and saleorderline.product_uom_qty = 0))" +
            " and crmteam.team_type = 'engine'")

        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            _logger.debug('create date : %r', query_result['create_date'])
            return query_result['create_date']
        else:
            return None

    # allocated product to customer
    def allocated_product_to_customer(self, customer_id,req_no, gl_account, customer_request_id, required_quantity, product_id, allocated_product_from_lot):
        allocated_product = {'customer_request_id':customer_request_id,'req_no':req_no, 'customer_required_quantity':required_quantity,
                                 'product_id':product_id, 'allocated_product_quantity':allocated_product_from_lot}
        # add data in allocated_product_for_gl_account_dict
        if gl_account and not gl_account is None:
            # match parent id and gl account
            res_partner = self.env['res.partner'].search([('gl_account', '=', gl_account),('parent_id', '=', customer_id)])
            if res_partner:
                if len(res_partner) == 1:
                    if res_partner.id in self.allocated_product_for_gl_account_dict.keys():
                        self.allocated_product_for_gl_account_dict.get(res_partner.id, {}).append(allocated_product)
                    else:
                        new_gl_account_key = {res_partner.id: [allocated_product]}
                        self.allocated_product_for_gl_account_dict.update(new_gl_account_key)
                else:
                    _logger.info('same gl account for multiple customer')
                    self.send_mail(str(gl_account) + " GL Account No presents for more than one contact.")
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
                _logger.info('customer_request_id  :  %r  ', allocated_product['customer_request_id'])

                sale_order_line_dict = {'customer_request_id': allocated_product['customer_request_id'],'req_no': allocated_product['req_no'], 'order_id': sale_order['id'], 'product_id': allocated_product['product_id'],
                                        'order_partner_id' : partner_id_key, 'product_uom_qty' : allocated_product['allocated_product_quantity']}

                self.env['sale.order.line'].create(dict(sale_order_line_dict))

            sale_order.force_quotation_send()
            print('**********Before action_confirm************', sale_order.state)
            sale_order.action_confirm()
            print('**********After action_confirm************', sale_order.state)
            _logger.info('sale order id  : %r  sale order state : %r', sale_order.id, sale_order.state)

            # picking = self.env['stock.picking'].search([('sale_id', '=', sale_order.id),('picking_type_id', '=', 1)])
            # _logger.info('picking state   : %r', picking.state)
            # picking.write({'state':'assigned'})
            # stock_move = self.env['stock.move'].search([('picking_id', '=', picking.id)])
            # stock_move.write({'state': 'assigned'})
            # sale_order.write(dict(state='engine', confirmation_date=''))
            # sale_order.force_quotation_send()
            sale_order.write({'state':'sent', 'confirmation_date':None})


    # Generate sale order for gl account
    def generate_sale_order_for_gl_account(self):
        _logger.info('In generate sale order for gl account %r', self.allocated_product_for_gl_account_dict)
        # get team id
        crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

        for partner_id_key in self.allocated_product_for_gl_account_dict.keys():
            _logger.info('partner id key : %r', partner_id_key)

            _logger.debug('res_partner : %r',partner_id_key)
            sale_order_dict = {'partner_id': partner_id_key, 'state': 'engine', 'team_id': crm_team['id']}

            sale_order = self.env['sale.order'].create(dict(sale_order_dict))
            _logger.debug('sale order : %r ', sale_order['id'])

            for allocated_product in self.allocated_product_for_gl_account_dict.get(partner_id_key, {}):
                sale_order_line_dict = {
                    'customer_request_id': allocated_product['customer_request_id'],'req_no': allocated_product['req_no'], 'order_id': sale_order['id'],
                    'product_id': allocated_product['product_id'],'order_partner_id': partner_id_key,
                    'product_uom_qty': allocated_product['allocated_product_quantity']}

                self.env['sale.order.line'].create(dict(sale_order_line_dict))

            sale_order.force_quotation_send()
            sale_order.action_confirm()
            _logger.info('sale order id  : %r  sale order state : %r', sale_order.id, sale_order.state)

            # picking = self.env['stock.picking'].search([('sale_id', '=', sale_order.id), ('picking_type_id', '=', 1)])
            # _logger.info('picking before   : %r', picking.state)
            # picking.write({'state':'assigned'})
            # stock_move = self.env['stock.move'].search([('picking_id', '=', picking.id)])
            # stock_move.write({'state': 'assigned'})
            # sale_order.write(dict(state='engine', confirmation_date=''))
            # sale_order.force_quotation_send()
            sale_order.write({'state':'sent', 'confirmation_date':''})

    # Change date format to calculate date difference (2018-06-25 23:08:15) to (2018, 6, 25, 23, 8, 15)
    def change_date_format(self, date):
        formatted_date = str(date).split(".")[0].replace("-", ",").replace(" ", ",").replace(":", ",")
        return formatted_date

    def get_available_product_count(self, customer_id, product_id):
        _logger.info("inside get_available_product_count")
        available_production_lot_dict =self.env['available.product.dict'].get_available_production_lot(customer_id, product_id)
        _logger.debug(available_production_lot_dict)
        count = 0
        if not available_production_lot_dict.get(int(product_id)) is None:
            for available_production_lot in available_production_lot_dict.get(int(product_id)):
                for available in available_production_lot:
                    count = count + available_production_lot.get(available).get('available_quantity')
        return count

    def check_product_threshold(self,prioritization_engine_request):
        if prioritization_engine_request['uom_flag']:
            min_threshold = prioritization_engine_request['min_threshold']
            max_threshold = prioritization_engine_request['max_threshold']
            inventory_quantity = prioritization_engine_request['quantity']
        else:
            product = self.env['product.template'].search([('id', '=', prioritization_engine_request['product_id'])])
            uom = self.env['uom.uom'].search([('name', 'ilike', 'Unit'),('category_id.id', '=', 1)])
            if len(uom) == 0:
                uom = self.env['uom.uom'].search([('name', 'ilike', 'Each'),('category_id.id', '=', 1)])
            min_threshold = product.manufacturer_uom._compute_quantity(float(prioritization_engine_request['min_threshold']), uom)
            max_threshold = product.manufacturer_uom._compute_quantity(float(prioritization_engine_request['max_threshold']), uom)
            inventory_quantity = product.manufacturer_uom._compute_quantity(float(prioritization_engine_request['quantity']), uom)
            if prioritization_engine_request['status'].lower().strip() == 'partial':
                sale_order_lines = self.env['sale.order.line'].search([('customer_request_id', '=', prioritization_engine_request['customer_request_id'])])
                product_uom_qty = 0
                for sale_order_line in sale_order_lines:
                    product_uom_qty = product_uom_qty + sale_order_line.product_uom_qty
                _logger.debug('sale_order_line.product_uom_qty : %r', product_uom_qty)
                inventory_quantity = inventory_quantity - product_uom_qty
                _logger.debug('inventory_quantity : %r', inventory_quantity)
                return True, inventory_quantity



        if int(inventory_quantity) < int(min_threshold):
            allocate_quantity = int(max_threshold) - int(inventory_quantity)
            return True,allocate_quantity
        else:
            self.update_customer_request_status(prioritization_engine_request, 'Inprocess')
            prioritization_engine_request['customer_request_logs'] += 'Unable to allocate product beacause stock is greater than minimum threshold, '
            return False,0

    # Update uploaded document status
    def _check_uploaded_document_status(self):
        # get all document whose status is draft and In Process.
        sps_cust_uploaded_documents = self.env['sps.cust.uploaded.documents'].search([('status', 'in', ('draft', 'In Process'))])

        for sps_cust_uploaded_document in sps_cust_uploaded_documents:
            _logger.info('Document Id :%r', sps_cust_uploaded_document.id)

            current_cust_doc_fixed_count = sps_cust_uploaded_document.customer_id['doc_process_count']
            current_processing_doc_id = sps_cust_uploaded_document.id
            current_processed_docs = sps_cust_uploaded_document.document_processed_count
            template = None
            sps_customer_requirement = self.env['sps.customer.requests'].search([('document_id', '=', sps_cust_uploaded_document.id), ('status', 'in', ['Partial', 'InCoolingPeriod', 'New', 'Inprocess', 'Incomplete', 'Unprocessed'])])
            sps_customer_requirements = self.env['sps.customer.requests'].search([('document_id', '=', sps_cust_uploaded_document.id), ('status', 'in', ['InCoolingPeriod', 'New', 'Inprocess', 'Incomplete', 'Unprocessed'])])
            sps_customer_requirements_all = self.env['sps.customer.requests'].search([('document_id', '=', sps_cust_uploaded_document.id), ('status', 'not in', ['Voided'])])

            if sps_cust_uploaded_document.template_type.lower().strip() == 'requirement':
                if current_processed_docs >= current_cust_doc_fixed_count:
                    self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')
                    if len(sps_customer_requirements) == len(sps_customer_requirements_all):
                        template = self.env.ref('customer-requests.final_email_response_on_uploaded_document').sudo()
                else:
                    if len(sps_customer_requirement) > 0:
                        if len(sps_customer_requirements) == len(sps_customer_requirements_all):
                            template = self.env.ref('customer-requests.email_response_on_uploaded_document').sudo()
                        if sps_cust_uploaded_document.status != 'In Process':
                            self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'In Process')
                    else:
                        if sps_cust_uploaded_document.status != 'Completed':
                            self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')

            elif sps_cust_uploaded_document.template_type.lower().strip() == 'inventory':
                if int(current_processed_docs) >= int(current_cust_doc_fixed_count):
                    self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')
                    if len(sps_customer_requirements) == len(sps_customer_requirements_all):
                        template = self.env.ref('customer-requests.final_email_response_on_uploaded_document').sudo()
                else:
                    if int(current_processing_doc_id) == int(sps_cust_uploaded_document.id):
                        if len(sps_customer_requirement) > 0:
                            if len(sps_customer_requirements) == len(sps_customer_requirements_all):
                                template = self.env.ref('customer-requests.email_response_on_uploaded_document').sudo()
                            if sps_cust_uploaded_document.status != 'In Process':
                                self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'In Process')
                        else:
                            if sps_cust_uploaded_document.status != 'Completed':
                                self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')
                    else:
                        if sps_cust_uploaded_document.status != 'Completed':
                            self._update_uploaded_document_status(sps_cust_uploaded_document.id, 'Completed')

            # Send Email Notification to customer about the progress of uploaded or sent document
            if template is not None:
                # Send Email
                self.send_mail(sps_cust_uploaded_document.customer_id.name, sps_cust_uploaded_document.customer_id.email, template)

    def _update_uploaded_document_status(self,document_id,status):
        try:
            self.env['sps.cust.uploaded.documents'].search([('id', '=', document_id)]).write({'status':status})
        except Exception:
            _logger.error("Unable to update document status")

    # Release reserved product quantity(Which sales order product not confirm within length of hold period)
    def release_reserved_product_quantity(self):
        _logger.info('release reserved product quantity....')
        # get team id
        crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

        sale_orders = self.env['sale.order'].search([('state', 'in', ('engine', 'sent', 'void')), ('team_id', '=', crm_team['id'])])

        for sale_order in sale_orders:
            _logger.info('sale order name : %r, partner_id : %r, create_date: %r', sale_order['name'], sale_order['partner_id'].id, sale_order['create_date'])

            stock_picking = self.env['stock.picking'].search([('sale_id.id', '=', sale_order['id'])])

            for stock_pick in stock_picking:
                stock_moves = self.env['stock.move'].search([('picking_id.id', '=', stock_pick['id'])])
                if stock_moves and len(stock_moves)>0:
                    for stock_move in  stock_moves:

                        # get length of hold
                        _setting_object = self.env['sps.customer.requests'].get_settings_object(sale_order['partner_id'].id, stock_move['product_id'].id, None, None)

                        _logger.info('length of hold %r', _setting_object.length_of_hold)

                        # get current datetime
                        current_datetime = datetime.now()

                        create_date = datetime.strptime(self.change_date_format(sale_order['create_date']), '%Y,%m,%d,%H,%M,%S')
                        # calculate datetime difference.
                        duration = current_datetime - create_date  # For build-in functions
                        duration_in_hours = self.return_duration_in_hours(duration)
                        if _setting_object and int(_setting_object.length_of_hold) <= int(duration_in_hours):
                            _logger.info('call stock_move._do_unreserve()')
                            stock_move._do_unreserve()
                        else:
                            _logger.info('Product is in length of hold, unable to release quantity.')
            self.change_sale_order_state(sale_order)

    # change sale order state: 'cancel' when length of hold of all products in sale order is finished.
    def change_sale_order_state(self,sale_order):
        _logger.info('In change_sale_order_state()')
        stock_picking = self.env['stock.picking'].search([('sale_id.id', '=', sale_order['id']),('picking_type_id', '=', 1)])
        _logger.info('stock picking id : %r ',stock_picking['id'])
        stock_move_lines = self.env['stock.move.line'].search([('picking_id.id', '=', stock_picking['id'])])
        _logger.info('stock_move_lines length : %r ', len(stock_move_lines))
        if len(stock_move_lines) == 0:
            _logger.info('sale order state before : %r', sale_order['state'])
            sale_order.action_cancel()
            _logger.info('sales order status after : %r', sale_order['state'])


    def send_mail(self, body):
        template = self.env.ref('prioritization_engine.set_log_gl_account_response').sudo()
        local_context = {'body': body}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
        except:
            response = {'message': 'Unable to connect to SMTP Server'}

    def send_mail(self, customerName, customerEmail, template):
        local_context = {'customerName': customerName, 'customerEmail': customerEmail}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
        except:
            response = {'message': 'Unable to connect to SMTP Server'}