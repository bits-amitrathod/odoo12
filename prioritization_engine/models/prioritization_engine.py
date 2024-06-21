from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime
import re

# from odoo import SUPERUSER_ID

SUPERUSER_ID = 2

_logger = logging.getLogger(__name__)


class PrioritizationEngine(models.TransientModel):
    # _inherit = 'crm.team'
    _name = 'prioritization.engine.model'

#     team_type = fields.Selection([('prioritization', 'Prioritization')])

    allocated_product_dict = {}
    allocated_product_for_gl_account_dict = {}

    def allocate_product_by_priority(self, customer_request_list, document_ids, source=None):
        if source == 'Portal':
            document = self.env['sps.cust.uploaded.documents'].search([('id', '=', document_ids[0])])
        self.allocated_product_dict.clear()
        self.allocated_product_for_gl_account_dict.clear()
        _logger.debug('In product_allocation_by_priority')
        _logger.info('Document Count: %d', len(document_ids))
        # get available production lot list.
        available_product_lot_dict = self.get_available_product_lot_dict(document_ids)
        if len(available_product_lot_dict) > 0:
            for customer_request in customer_request_list:
                # auto allocate True/False
                if customer_request.auto_allocate:
                    # customer_request.write({'customer_request_logs': 'Auto allocate is true, '})
                    _logger.debug('Auto allocate is true.')
                    filter_available_product_lot_dict = self.filter_available_product_lot_dict(
                        available_product_lot_dict, customer_request.product_id.id,
                        customer_request.expiration_tolerance)
                    if len(filter_available_product_lot_dict) > 0:
                        # check cooling period- method return True/False
                        if self.check_cooling_period(customer_request):
                            # customer_request.write({'customer_request_logs': str(customer_request.customer_request_logs) + 'success cooling period, '})
                            _logger.debug('success cooling period')
                            if customer_request.document_id.template_type.lower().strip() == 'inventory':
                                # check min-max threshold
                                _logger.debug('Template type is Inventory.')
                                flag, allocate_inventory_product_quantity = self.check_product_threshold(
                                    customer_request)
                                if flag:
                                    # allocate product
                                    self.allocate_product(customer_request, filter_available_product_lot_dict,
                                                          allocate_inventory_product_quantity)
                            else:
                                # allocate product
                                self.allocate_product(customer_request, filter_available_product_lot_dict, None)
                        else:
                            customer_request.write({'customer_request_logs': str(
                                customer_request.customer_request_logs) + 'In Cooling period.'})
                            _logger.debug('Cooling period false.....')
                    else:
                        customer_request.write({'customer_request_logs': str(
                            customer_request.customer_request_logs) + 'As per requested expiration tolerance product lot not available.'})
                        if customer_request.status.lower().strip() != 'Inprocess' and customer_request.status.lower().strip() != 'partial':
                            customer_request.write({'status': 'Inprocess'})
                        _logger.debug('As per requested expiration tolerance product lot not available.')
                else:
                    customer_request.write({'customer_request_logs': str(
                        customer_request.customer_request_logs) + 'Auto allocate is false.'})
                    _logger.debug('Auto allocate is false.')
            if len(self.allocated_product_dict) > 0:
                self.generate_sale_order(self.allocated_product_dict)
                if source == 'Portal' and document:
                    document.write({'document_logs': 'Sales order created'})
            if len(self.allocated_product_for_gl_account_dict) > 0:
                self.generate_sale_order(self.allocated_product_for_gl_account_dict)
            # self.env['available.product.dict'].update_production_lot_dict()
        else:
            _logger.debug('Available product lot list is zero')

    # get available production lot list, parameter product id.
    def get_available_product_lot_dict(self, document_ids):
        production_lot_dict = self.env['available.product.dict'].get_available_production_lot_dict(document_ids)
        return production_lot_dict

    def filter_available_product_lot_dict(self, available_production_lot_dict, product_id, expiration_tolerance):
        filtered_production_lot_dict_to_be_returned = {}
        filtered_production_lot_dict_to_be_returned.clear()
        for available_production_lot in available_production_lot_dict.get(product_id, {}):
            if datetime.strptime(
                    str(available_production_lot.get(list(available_production_lot.keys()).pop(0), {}).get('use_date')),
                    '%Y-%m-%d %H:%M:%S') >= self.get_product_expiration_tolerance_date(expiration_tolerance):

                if product_id in filtered_production_lot_dict_to_be_returned.keys():
                    filtered_production_lot_dict_to_be_returned.get(product_id, {}).append(available_production_lot)
                else:
                    dict = {product_id: [available_production_lot]}
                    filtered_production_lot_dict_to_be_returned.update(dict)

        _logger.debug('Filtered production lot list to be returned %r',
                      str(filtered_production_lot_dict_to_be_returned))
        return filtered_production_lot_dict_to_be_returned

    # calculate cooling period
    def check_cooling_period(self, customer_request):
        flag = True
        if self.check_length_of_hold(customer_request):
            # get product create date
            create_date = self.get_product_create_date(customer_request)
            if create_date is not None:
                # get current datetime
                current_datetime = datetime.now()
                create_date = datetime.strptime(self.change_date_format(create_date), '%Y,%m,%d,%H,%M,%S')
                # convert cooling period days into hours
                cooling_period_in_hours = int(customer_request.cooling_period) * 24
                # length_of_hold_in_hours = int(customer_request.length_of_hold)
                total_hours = cooling_period_in_hours  # + length_of_hold_in_hours
                # calculate datetime difference.
                duration = current_datetime - create_date  # For build-in functions
                duration_in_hours = self.return_duration_in_hours(duration)
                if int(total_hours) <= int(duration_in_hours):
                    _logger.info('True')
                    if customer_request.status.lower().strip() != 'inprocess':
                        customer_request.write({'status': 'Inprocess'})
                    flag = True
                else:
                    if customer_request.status.lower().strip() != 'incoolingperiod' and customer_request.status.lower().strip() != 'partial':
                        customer_request.write({'status': 'InCoolingPeriod'})
                    flag = False
            else:
                flag = True
        else:
            # Product is in cooling period.
            flag = False
        return flag

    # calculate length of hold(In hours)
    def check_length_of_hold(self, customer_request):
        flag = True
        # get previous sales order create date
        create_date = self._get_product_create_date(customer_request)
        if create_date is not None:
            # get current datetime
            current_datetime = datetime.now()
            create_date = datetime.strptime(self.change_date_format(create_date), '%Y,%m,%d,%H,%M,%S')
            # calculate datetime difference.
            duration = current_datetime - create_date  # For build-in functions
            # duration_in_hours = self.return_duration_in_hours(duration)
            duration_in_minutes = self.return_duration_in_minutes(duration)

            # if int(customer_request.length_of_hold) <= int(duration_in_hours):
            if int(customer_request.length_of_hold) <= int(duration_in_minutes):
                flag = True
            else:
                # update status In cooling period
                if customer_request.status.lower().strip() != 'incoolingperiod' and customer_request.status.lower().strip() != 'partial':
                    customer_request.write({'status': 'InCoolingPeriod'})
                flag = False
        else:
            flag = True
        return flag

    # get product expiration tolerance date, expiration tolerance in months(3/6/12)
    @staticmethod
    def get_product_expiration_tolerance_date(expiration_tolerance):
        expiration_tolerance_date = datetime.today() + relativedelta(months=+int(expiration_tolerance))
        return expiration_tolerance_date

    # Allocate product
    def allocate_product(self, customer_request, filter_available_product_lot_dict,
                         allocate_inventory_product_quantity):
        if customer_request.document_id.template_type.lower().strip() == 'inventory':
            required_quantity = allocate_inventory_product_quantity
            remaining_product_allocation_quantity = allocate_inventory_product_quantity
        else:
            required_quantity = customer_request.updated_quantity
            remaining_product_allocation_quantity = customer_request.updated_quantity
        for product_lot in filter_available_product_lot_dict.get(customer_request.product_id.id, {}):
            _logger.debug('**** %r', product_lot.get(list(product_lot.keys()).pop(0), {}).get('available_quantity'))

            if int(remaining_product_allocation_quantity) > 0 and int(
                    product_lot.get(list(product_lot.keys()).pop(0), {}).get('available_quantity')) > 0:
                if int(remaining_product_allocation_quantity) > int(
                        product_lot.get(list(product_lot.keys()).pop(0), {}).get('available_quantity')):
                    if customer_request.partial_ordering:
                        if customer_request.uom_flag:
                            _logger.debug('product allocated from lot %r %r %r',
                                          product_lot.get(list(product_lot.keys()).pop(0), {}))

                            remaining_product_allocation_quantity = int(remaining_product_allocation_quantity) - int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                            product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])
                            product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0
                        else:
                            if customer_request.partial_UOM:
                                remaining_product_allocation_quantity = int(
                                    remaining_product_allocation_quantity) - int(
                                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])

                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(
                                    product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(
                                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'])
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = 0
                            else:
                                allocate_qty_by_partial_uom = self._get_quantity_by_partial_uom(
                                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'],
                                    customer_request)

                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(
                                    product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(
                                    allocate_qty_by_partial_uom)
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(
                                    product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(
                                    allocate_qty_by_partial_uom)

                                remaining_product_allocation_quantity = remaining_product_allocation_quantity - allocate_qty_by_partial_uom

                elif int(remaining_product_allocation_quantity) <= int(
                        product_lot.get(list(product_lot.keys()).pop(0), {}).get('available_quantity')):
                    _logger.debug('product allocated from lot %r', list(product_lot.keys()).pop(0))

                    if customer_request.uom_flag:
                        product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(
                            product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(
                            remaining_product_allocation_quantity)
                        product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(
                            product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(
                            remaining_product_allocation_quantity)

                        remaining_product_allocation_quantity = 0
                        break
                    else:
                        if customer_request.partial_UOM:
                            product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(
                                remaining_product_allocation_quantity)
                            product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(
                                remaining_product_allocation_quantity)

                            remaining_product_allocation_quantity = 0
                            break
                        else:
                            if customer_request.product_id.product_tmpl_id.uom_id.name in ['Each', 'Unit']:
                                allocate_qty_by_partial_uom = self._get_quantity_by_partial_uom(
                                    remaining_product_allocation_quantity, customer_request)
                            else:
                                allocate_qty_by_partial_uom = remaining_product_allocation_quantity
                            product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity'] = int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['reserved_quantity']) + int(
                                allocate_qty_by_partial_uom)
                            product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity'] = int(
                                product_lot.get(list(product_lot.keys()).pop(0), {})['available_quantity']) - int(
                                allocate_qty_by_partial_uom)

                            remaining_product_allocation_quantity = remaining_product_allocation_quantity - allocate_qty_by_partial_uom
                            break

        if customer_request.document_id.template_type.lower().strip() == 'inventory':
            if remaining_product_allocation_quantity == allocate_inventory_product_quantity:
                self._update_logs(customer_request)
        elif remaining_product_allocation_quantity == customer_request.updated_quantity:
            self._update_logs(customer_request)

        if remaining_product_allocation_quantity == 0:
            _logger.debug("Allocated all required product quantity.")

            self.allocated_product_to_customer(customer_request.customer_id.id,
                                               customer_request.document_id.source,
                                               customer_request.req_no,
                                               customer_request.req_date,
                                               customer_request.vendor,
                                               customer_request.item_no,
                                               customer_request.deliver_to_location,
                                               customer_request.gl_account,
                                               customer_request.id,
                                               required_quantity,
                                               customer_request.product_id.id,
                                               required_quantity,
                                               'Fulfilled')

            # Update updated_quantity
            if customer_request.document_id.template_type.lower().strip() == 'requirement':
                customer_request.write({'updated_quantity': remaining_product_allocation_quantity})

        elif remaining_product_allocation_quantity > 0 and remaining_product_allocation_quantity != required_quantity:
            _logger.debug(str(" Allocated Partial order product."))

            self.allocated_product_to_customer(customer_request.customer_id.id,
                                               customer_request.document_id.source,
                                               customer_request.req_no,
                                               customer_request.req_date,
                                               customer_request.vendor,
                                               customer_request.item_no,
                                               customer_request.deliver_to_location,
                                               customer_request.gl_account,
                                               customer_request.id,
                                               required_quantity,
                                               customer_request.product_id.id,
                                               required_quantity - remaining_product_allocation_quantity,
                                               'Partial')

            self._update_logs(customer_request)

            # Update updated_quantity
            if customer_request.document_id.template_type.lower().strip() == 'requirement':
                customer_request.write({'updated_quantity': remaining_product_allocation_quantity})

    # Update Prioritization Engine logs.
    @staticmethod
    def _update_logs(customer_request):
        if customer_request.partial_ordering:
            # customer_request.write({'customer_request_logs': str(customer_request.customer_request_logs) + 'Partial ordering flag is True.'})
            _logger.debug('Partial ordering flag is True')
            if customer_request.partial_UOM:
                # customer_request.write({'customer_request_logs': str(customer_request.customer_request_logs) + 'Partial UOM flag is True.'})
                _logger.debug('Partial UOM is True')
            else:
                customer_request.write({'customer_request_logs': str(
                    customer_request.customer_request_logs) + 'Partial UOM flag is False.'})
                _logger.debug('Partial UOM is False')
        else:
            customer_request.write({'customer_request_logs': str(
                customer_request.customer_request_logs) + 'Partial ordering flag is False.'})
            _logger.debug('Partial ordering flag is False')

    # get quantity by partial uom flag
    def _get_quantity_by_partial_uom(self, quantity, customer_request):
        product = self.env['product.template'].search([('id', '=', customer_request.product_id.product_tmpl_id.id)])

        if product.manufacturer_uom.uom_type == 'bigger':
            uom_factor = product.manufacturer_uom.factor_inv
        elif product.manufacturer_uom.uom_type == 'smaller':
            uom_factor = product.manufacturer_uom.factor
        else:
            uom_factor = 1

        ratio = int(quantity / uom_factor)
        allocate_qty_by_partial_uom = int(product.manufacturer_uom._compute_quantity(float(ratio), product.uom_id))
        return allocate_qty_by_partial_uom

    # update customer status
    def update_customer_request_status(self, customer_request_id, status, req_log):
        customer_req = self.env['sps.customer.requests'].search([('id', '=', customer_request_id)])
        customer_req.write(
            {'status': status, 'customer_request_logs': str(customer_req.customer_request_logs) + req_log})

    # get product create date for to calculate length of hold and cooling period.
    def get_product_create_date(self, customer_request):
        self.env.cr.execute(
            "SELECT max(saleorder.create_date) as create_date FROM public.sale_order_line saleorderline "
            " INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " INNER JOIN public.crm_team crmteam ON crmteam.id = saleorder.team_id"
            " WHERE saleorderline.order_partner_id IN (SELECT distinct unnest(array[id, parent_id]) from public.res_partner WHERE parent_id = " +
            str(customer_request.customer_id.id) + " or id = " + str(customer_request.customer_id.id) + " ) " +
            " and saleorderline.product_id = " + str(customer_request.product_id.id) +
            " and ((saleorder.state in ('engine','sent','cancel')) or (saleorder.state in ('sent','sale') and saleorderline.product_uom_qty = 0))" +
            " and crmteam.team_type in ('engine','rapid_quote')")

        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            _logger.debug('create date : %r', query_result['create_date'])
            return query_result['create_date']
        else:
            return None

    # get product create date for to calculate length of hold.
    def _get_product_create_date(self, customer_request):
        self.env.cr.execute(
            "SELECT max(saleorder.create_date) as create_date FROM public.sale_order_line saleorderline "
            " INNER JOIN public.sale_order saleorder ON saleorder.id = saleorderline.order_id "
            " INNER JOIN public.crm_team crmteam ON crmteam.id = saleorder.team_id"
            " WHERE saleorderline.order_partner_id IN (SELECT distinct unnest(array[id, parent_id]) from public.res_partner WHERE parent_id = " +
            str(customer_request.customer_id.id) + " or id = " + str(customer_request.customer_id.id) + " ) " +
            " and saleorderline.product_id = " + str(customer_request.product_id.id) +
            " and ((saleorder.state in ('engine','sent')) or (saleorder.state in ('sent','sale') and saleorderline.product_uom_qty = 0))" +
            " and crmteam.team_type in ('engine','rapid_quote')")

        query_result = self.env.cr.dictfetchone()

        if query_result['create_date'] != None:
            _logger.debug('create date : %r', query_result['create_date'])
            return query_result['create_date']
        else:
            return None

    # allocated product to customer
    def allocated_product_to_customer(self, customer_id, document_source, req_no, req_date, vendor, item_no, deliver_to_location,
                                      gl_account, customer_request_id, required_quantity,
                                      product_id, allocated_product_from_lot, cust_req_status):
        allocated_product = {'customer_request_id': customer_request_id, 'document_source': document_source, 'req_no': req_no,
                             'req_date': req_date, 'vendor': vendor, 'item_no': item_no,
                             'deliver_to_location': deliver_to_location,
                             'customer_required_quantity': required_quantity,
                             'product_id': product_id, 'allocated_product_quantity': allocated_product_from_lot,
                             'cust_req_status': cust_req_status}
        # add data in allocated_product_for_gl_account_dict
        if gl_account and gl_account is not None:
            # match parent id and gl account
            res_partner = self.env['res.partner'].search(
                [('gl_account', '=', gl_account), ('parent_id', '=', customer_id)])
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
    @staticmethod
    def return_duration_in_days(duration):
        duration_in_seconds = int(duration.total_seconds())
        duration_in_hours = duration_in_seconds / 3600
        duration_in_days = int(duration_in_hours) / 24
        return int(duration_in_days)

    # return duration in hours
    @staticmethod
    def return_duration_in_hours(duration):
        duration_in_seconds = int(duration.total_seconds())
        duration_in_hours = duration_in_seconds / 3600
        return int(duration_in_hours)

    # return duration in minutes
    @staticmethod
    def return_duration_in_minutes(duration):
        duration_in_seconds = int(duration.total_seconds())
        duration_in_mintues = duration_in_seconds / 60
        return int(duration_in_mintues)

    # Generate sale order
    def generate_sale_order(self, allocated_products_dict):
        _logger.debug('In generate sale order %r', allocated_products_dict)
        for partner_id_key in allocated_products_dict.keys():
            # get team id
            if allocated_products_dict.get(partner_id_key, {})[0]['document_source'] == 'Portal':
                crm_team = self.env['crm.team'].search([('team_type', '=', 'rapid_quote')])
            else:
                crm_team = self.env['crm.team'].search([('team_type', '=', 'engine')])

            if partner_id_key:
                partner_obj = self.env['res.partner'].search([('id', '=', partner_id_key)])
                if partner_obj.property_payment_term_id:
                    sale_order_dict = {'partner_id': partner_id_key, 'payment_term_id': partner_obj.property_payment_term_id.id
                        , 'state': 'draft', 'team_id': crm_team['id']}
                else:
                    sale_order_dict = {'partner_id': partner_id_key, 'state': 'draft', 'team_id': crm_team['id']}

            #sale_order_dict = {'partner_id': partner_id_key, 'state': 'draft', 'team_id': crm_team['id']}
            try:
                self.env.cr.savepoint()
                sale_order = self.env['sale.order'].create(dict(sale_order_dict))
                _logger.debug('sale order : %r ', sale_order['id'])
                for allocated_product in allocated_products_dict.get(partner_id_key, {}):
                    _logger.info('customer_request_id  :  %r  ', allocated_product['customer_request_id'])

                    sale_order_line_dict = {'customer_request_id': allocated_product['customer_request_id'],
                                            'req_no': allocated_product['req_no'], 'order_id': sale_order['id'],
                                            'req_date': allocated_product['req_date'],
                                            'vendor': allocated_product['vendor'],
                                            'item_no': allocated_product['item_no'],
                                            'deliver_to_location': allocated_product['deliver_to_location'],
                                            'product_id': allocated_product['product_id'],
                                            'order_partner_id': partner_id_key,
                                            'product_uom_qty': allocated_product['allocated_product_quantity']}

                    sale_order_line = self.env['sale.order.line'].create(dict(sale_order_line_dict))
                    # TODO: UPD ODOO16 Discount Cal Method Changed in parent we need to check this
                    # discount = sale_order_line.get_discount()
                    #
                    # if discount and discount > 0.0:
                    #     sale_order_line.write({'discount': discount})

                    if allocated_product['cust_req_status'] == 'Fulfilled':
                        self.update_customer_request_status(allocated_product['customer_request_id'], 'Fulfilled',
                                                            'Product allocated.')
                    elif allocated_product['cust_req_status'] == 'Partial':
                        self.update_customer_request_status(allocated_product['customer_request_id'], 'Partial',
                                                            ' Allocated Partial order product.')

                _logger.info('**********Before action_confirm************ : %r', sale_order.state)
                sale_order.action_confirm()
                sale_order.write({'state': 'draft'})
                _logger.info('**********Before _send_order_confirmation_mail() ************  :  %r', sale_order.state)
                sale_order.force_quotation_send()
                _logger.info('sale order name  : %r  sale order state : %r', sale_order.name, sale_order.state)
                # sale_order.write({'state': 'sent'}) # removed from odoo 14 'confirmation_date': None
                _logger.info('changed sales order state : %r', sale_order.state)
                self.env.cr.commit()
            except Exception as exc:
                _logger.error("getting error while creation of sales order : %r", exc)
                self.env.cr.rollback()

    # Change date format to calculate date difference (2018-06-25 23:08:15) to (2018, 6, 25, 23, 8, 15)
    @staticmethod
    def change_date_format(date):
        formatted_date = str(date).split(".")[0].replace("-", ",").replace(" ", ",").replace(":", ",")
        return formatted_date

    def get_available_product_count(self, customer_id, product_id):
        _logger.info("inside get_available_product_count")
        available_production_lot_dict = self.env['available.product.dict'].get_available_production_lot(customer_id,
                                                                                                        product_id)
        _logger.debug(available_production_lot_dict)
        count = 0
        if not available_production_lot_dict.get(int(product_id)) is None:
            for available_production_lot in available_production_lot_dict.get(int(product_id)):
                for available in available_production_lot:
                    count = count + available_production_lot.get(available).get('available_quantity')
        return count

    def check_product_threshold(self, customer_request):
        if customer_request.uom_flag:
            min_threshold = customer_request.min_threshold
            max_threshold = customer_request.max_threshold
            inventory_quantity = customer_request.quantity
        else:
            product = self.env['product.template'].search([('id', '=', customer_request.product_id.product_tmpl_id.id)])

            min_threshold = product.manufacturer_uom._compute_quantity(float(customer_request.min_threshold),
                                                                       product.uom_id)
            max_threshold = product.manufacturer_uom._compute_quantity(float(customer_request.max_threshold),
                                                                       product.uom_id)
            inventory_quantity = product.manufacturer_uom._compute_quantity(float(customer_request.quantity),
                                                                            product.uom_id)
            if customer_request.status.lower().strip() == 'partial':
                sale_order_lines = self.env['sale.order.line'].search(
                    [('customer_request_id', '=', customer_request.id)])
                product_uom_qty = 0
                for sale_order_line in sale_order_lines:
                    product_uom_qty = product_uom_qty + sale_order_line.product_uom_qty
                _logger.debug('sale_order_line.product_uom_qty : %r', product_uom_qty)
                inventory_quantity = inventory_quantity - product_uom_qty
                _logger.debug('inventory_quantity : %r', inventory_quantity)
                return True, inventory_quantity
        if int(inventory_quantity) < int(min_threshold):
            allocate_quantity = int(max_threshold) - int(inventory_quantity)
            return True, allocate_quantity
        else:
            customer_request.write({'customer_request_logs': str(
                customer_request.customer_request_logs) + 'Unable to allocate product because stock is greater than minimum threshold, '})
            return False, 0

    # Update uploaded document status
    def check_uploaded_document_status(self, document_id):
        if document_id is not None:
            sps_cust_uploaded_documents = self.env['sps.cust.uploaded.documents'].search([('id', '=', document_id)])
        else:
            # get all document whose status is draft and In Process.
            sps_cust_uploaded_documents = self.env['sps.cust.uploaded.documents'].search(
                [('status', 'in', ('draft', 'In Process'))])

        if len(sps_cust_uploaded_documents) > 0:
            for sps_cust_uploaded_document in sps_cust_uploaded_documents:
                _logger.info('Document Id :%r', sps_cust_uploaded_document.id)

                current_cust_doc_fixed_count = sps_cust_uploaded_document.customer_id['doc_process_count']
                current_processing_doc_id = sps_cust_uploaded_document.id
                current_processed_docs = sps_cust_uploaded_document.document_processed_count
                template = None
                sps_customer_requirement = self.env['sps.customer.requests'].search(
                    [('document_id', '=', sps_cust_uploaded_document.id),
                     ('status', 'in', ['Partial', 'InCoolingPeriod', 'New', 'Inprocess', 'Incomplete', 'Unprocessed'])])
                sps_customer_requirements = self.env['sps.customer.requests'].search(
                    [('document_id', '=', sps_cust_uploaded_document.id),
                     ('status', 'in', ['InCoolingPeriod', 'New', 'Inprocess', 'Incomplete', 'Unprocessed'])])
                sps_customer_requirements_all_non_voided = self.env['sps.customer.requests'].search(
                    [('document_id', '=', sps_cust_uploaded_document.id), ('status', 'not in', ['Voided'])])
                high_priority_requests = self.env['sps.customer.requests'].search(
                    [('document_id', '=', sps_cust_uploaded_document.id), ('status', 'in', ['New']),
                     ('priority', '=', 0), ('available_qty', '>', 0)])

                if sps_cust_uploaded_document.template_type.lower().strip() == 'requirement':
                    if int(current_processed_docs) >= int(current_cust_doc_fixed_count):
                        sps_cust_uploaded_document.write({'status': 'Completed'})
                        self._update_all_request_status(sps_cust_uploaded_document)
                        if len(sps_customer_requirements) == len(sps_customer_requirements_all_non_voided):
                            template = self.env.ref(
                                'customer-requests.final_email_response_on_uploaded_document').sudo()
                            if sps_cust_uploaded_document.source == 'Portal':
                                sps_cust_uploaded_document.write({'document_logs': 'Unfortunately, we are currently out of stock on the products that you requested. We have documented your request on your account.'})
                    else:
                        if len(sps_customer_requirement) > 0:
                            if sps_cust_uploaded_document.status == 'In Process' and len(
                                    sps_customer_requirements) == len(sps_customer_requirements_all_non_voided):
                                template = self.env.ref('customer-requests.email_response_on_uploaded_document').sudo()
                                if sps_cust_uploaded_document.source == 'Portal':
                                    sps_cust_uploaded_document.write({'document_logs': 'Unfortunately, we are currently out of stock on the products that you requested. We have documented your request on your account.'})
                            if sps_cust_uploaded_document.status == 'draft' and len(high_priority_requests) == 0:
                                sps_cust_uploaded_document.write({'status': 'In Process'})
                                if len(sps_customer_requirements) == len(sps_customer_requirements_all_non_voided):
                                    template = self.env.ref(
                                        'customer-requests.email_response_on_uploaded_document').sudo()
                                    if sps_cust_uploaded_document.source == 'Portal':
                                        sps_cust_uploaded_document.write({'document_logs': 'Unfortunately, we are currently out of stock on the products that you requested. We have documented your request on your account.'})
                        else:
                            sps_cust_uploaded_document.write({'status': 'Completed'})

                elif sps_cust_uploaded_document.template_type.lower().strip() == 'inventory':
                    if int(current_processed_docs) >= int(current_cust_doc_fixed_count):
                        sps_cust_uploaded_document.write({'status': 'Completed'})
                        self._update_all_request_status(sps_cust_uploaded_document)
                        if len(sps_customer_requirements) == len(sps_customer_requirements_all_non_voided):
                            template = self.env.ref(
                                'customer-requests.final_email_response_on_uploaded_document').sudo()
                    else:
                        if int(current_processing_doc_id) == int(sps_cust_uploaded_document.id):
                            if len(sps_customer_requirement) > 0:
                                if sps_cust_uploaded_document.status == 'In Process' and len(
                                        sps_customer_requirements) == len(sps_customer_requirements_all_non_voided):
                                    template = self.env.ref(
                                        'customer-requests.email_response_on_uploaded_document').sudo()
                                if sps_cust_uploaded_document.status == 'draft' and len(high_priority_requests) == 0:
                                    sps_cust_uploaded_document.write({'status': 'In Process'})
                                    if len(sps_customer_requirements) == len(sps_customer_requirements_all_non_voided):
                                        template = self.env.ref(
                                            'customer-requests.email_response_on_uploaded_document').sudo()
                            else:
                                sps_cust_uploaded_document.write({'status': 'Completed'})
                        else:
                            sps_cust_uploaded_document.write({'status': 'Completed'})
                            self._update_all_request_status(sps_cust_uploaded_document)

                # Send Email Notification to customer about the progress of uploaded or sent document
                if template is not None:
                    # Send Email
                    if sps_cust_uploaded_document.customer_id.user_id and sps_cust_uploaded_document.customer_id.user_id.partner_id and \
                            sps_cust_uploaded_document.customer_id.user_id.partner_id.email and sps_cust_uploaded_document.customer_id.account_manager_cust and \
                            sps_cust_uploaded_document.customer_id.account_manager_cust.partner_id and \
                            sps_cust_uploaded_document.customer_id.account_manager_cust.partner_id.email:
                        self.send_mail(sps_cust_uploaded_document.customer_id.name,
                                       sps_cust_uploaded_document.customer_id.email,
                                       sps_cust_uploaded_document.customer_id.user_id.partner_id.email,
                                       sps_cust_uploaded_document.customer_id.account_manager_cust.partner_id.email, template)
                    elif sps_cust_uploaded_document.customer_id.user_id and sps_cust_uploaded_document.customer_id.user_id.partner_id \
                            and sps_cust_uploaded_document.customer_id.user_id.partner_id.email:
                        self.send_mail(sps_cust_uploaded_document.customer_id.name,
                                       sps_cust_uploaded_document.customer_id.email,
                                       sps_cust_uploaded_document.customer_id.user_id.partner_id.email, '', template)
                    elif sps_cust_uploaded_document.customer_id.account_manager_cust and \
                            sps_cust_uploaded_document.customer_id.account_manager_cust.partner_id \
                            and sps_cust_uploaded_document.customer_id.account_manager_cust.partner_id.email:
                        self.send_mail(sps_cust_uploaded_document.customer_id.name,
                                       sps_cust_uploaded_document.customer_id.email,
                                       '', sps_cust_uploaded_document.customer_id.account_manager_cust.partner_id.email,
                                       template)
                    else:
                        self.send_mail(sps_cust_uploaded_document.customer_id.name,
                                       sps_cust_uploaded_document.customer_id.email, '', '', template)

    @staticmethod
    def _update_all_request_status(sps_cust_uploaded_document):
        for request in sps_cust_uploaded_document.request_ids:
            if request.status not in ('Fulfilled', 'Partial', 'Voided'):
                request.write({'status': 'Unprocessed'})

    # Release reserved product quantity(Which sales order product not confirm within length of hold period)
    def release_reserved_product_quantity(self):
        _logger.info('release reserved product quantity....')

        sale_orders = self.env['sale.order'].search(
            [('state', 'in', ('engine', 'sent', 'void')), ('team_id.team_type', 'in', ('engine', 'rapid_quote'))], order="id asc")

        for sale_order in sale_orders:
            _logger.info('sale order name : %r, partner_id : %r, create_date: %r', sale_order['name'],
                         sale_order['partner_id'].id, sale_order['create_date'])

            for stock_pick in sale_order.picking_ids:
                if stock_pick.state == 'assigned':
                    if stock_pick.move_line_ids and len(stock_pick.move_line_ids) > 0:
                        for stock_move in stock_pick.move_line_ids:
                            # get length of hold
                            _setting_object = self.env['sps.customer.requests'].get_settings_object(
                                sale_order['partner_id'].id, stock_move['product_id'].id)
                            if _setting_object and _setting_object is not None:
                                _logger.info('length of hold %r', _setting_object.length_of_hold)
                                # get current datetime
                                current_datetime = datetime.now()
                                create_date = datetime.strptime(self.change_date_format(sale_order['create_date']),
                                                                '%Y,%m,%d,%H,%M,%S')
                                # calculate datetime difference.
                                duration = current_datetime - create_date  # For build-in functions
                                #duration_in_hours = self.return_duration_in_hours(duration)
                                duration_in_minutes = self.return_duration_in_minutes(duration)
                                if _setting_object and int(_setting_object.length_of_hold) <= int(duration_in_minutes):
                                    # TODO: UPD_ODOO16_Note _do_unreserve is removed
                                    # _logger.info('call stock_move._do_unreserve()')
                                    # stock_move._do_unreserve()
                                    pass
                                else:
                                    _logger.info('Product is in length of hold, unable to release quantity.')
            self.change_sale_order_state(sale_order)

    # change sale order state: 'cancel' when length of hold of all products in sale order is finished.
    @staticmethod
    def change_sale_order_state(sale_order):
        for stock_pick in sale_order.picking_ids:
            if stock_pick.picking_type_id.name == 'Pick':
                _logger.info('stock picking id : %r ', stock_pick.picking_type_id.id)
                if len(stock_pick.move_line_ids) == 0:
                    _logger.info('sale order state before : %r', sale_order['state'])
                    sale_order.action_cancel()
                    _logger.info('sales order status after : %r', sale_order['state'])

    def send_mail(self, body):
        template = self.env.ref('prioritization_engine.set_log_gl_account_response').sudo()
        local_context = {'body': body}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=False, )
        except Exception as exc:
            _logger.error("getting error while sending email of sales order : %r", exc)
            response = {'message': 'Unable to connect to SMTP Server'}

    def send_mail(self, customerName, customerEmail, salespersonEmail, keyAccountEmail, template):
        local_context = {'customerName': customerName, 'customerEmail': customerEmail,
                         'salespersonEmail': salespersonEmail, 'keyAccountEmail': keyAccountEmail}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
        except Exception as exc:
            _logger.error("getting error while sending email of sales order : %r", exc)
            response = {'message': 'Unable to connect to SMTP Server'}