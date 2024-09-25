import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import pdf

from .fedex_request import FedexRequest
# Why using standardized ISO codes? It's way more fun to use made up codes...
# https://www.fedex.com/us/developer/WebHelp/ws/2014/dvg/WS_DVG_WebHelp/Appendix_F_Currency_Codes.htm
FEDEX_CURR_MATCH = {
    u'UYU': u'UYP',
    u'XCD': u'ECD',
    u'MXN': u'NMP',
    u'KYD': u'CID',
    u'CHF': u'SFR',
    u'GBP': u'UKL',
    u'IDR': u'RPA',
    u'DOP': u'RDD',
    u'JPY': u'JYE',
    u'KRW': u'WON',
    u'SGD': u'SID',
    u'CLP': u'CHP',
    u'JMD': u'JAD',
    u'KWD': u'KUD',
    u'AED': u'DHS',
    u'TWD': u'NTD',
    u'ARS': u'ARN',
    u'LVL': u'EURO',
}

_logger = logging.getLogger(__name__)


class FedexDelivery(models.Model):
    _inherit = 'delivery.carrier'

    def fedex_send_shipping_label(self, order, popup):
        res = []
        srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)
        srm.transaction_detail(order.id)
        package_type = popup.product_packaging.shipper_package_code or self.fedex_default_package_type_id.shipper_package_code
        srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit,
                             self.fedex_saturday_delivery)
        srm.shipment_request_email(order)
        srm.set_currency(_convert_curr_iso_fdx(order.currency_id.name))
        srm.set_shipper(order.partner_id, order.partner_id)
        # srm.set_recipient(order.company_id.partner_id)
        super_user = self.env['res.users'].browse(1)
        # print(super_user.partner_id.name)
        srm.set_recipient(super_user.partner_id)
        srm.shipping_charges_payment(superself.fedex_account_number)
        srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type,
                           'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')
        order_currency = order.currency_id
        net_weight = _convert_weight(popup.weight, 'LB')

        # Commodities for customs declaration (international shipping)
        if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (
                order.partner_id.country_id.code == 'IN' and order.company_id.partner_id.country_id.code == 'IN'):
            commodity_currency = order_currency
            total_commodities_amount = 0.0
            commodity_country_of_manufacture = order.company_id.partner_id.country_id.code

            '''for operation in picking.move_line_ids:
                commodity_amount = order_currency.compute(operation.product_id.list_price, commodity_currency)
                total_commodities_amount += (commodity_amount * operation.qty_done)
                commodity_description = operation.product_id.name
                commodity_number_of_piece = '1'
                commodity_weight_units = self.fedex_weight_unit
                commodity_weight_value = _convert_weight(operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
                commodity_quantity = operation.qty_done
                commodity_quantity_units = 'EA'
            srm.commodities(_convert_curr_iso_fdx(currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units)
            #srm.commodities(_convert_curr_iso_fdx('LB'), 0, '1',
                            'LB', 10, 'test',
                            commodity_country_of_manufacture, 1, 'EA')'''
            srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.company_id.partner_id.country_id.code, superself.fedex_account_number)

        package_count = popup.package_count

        # TODO RIM master: factorize the following crap

        ################
        # Multipackage #
        ################
        if package_count > 1:
            # Note: Fedex has a complex multi-piece shipping interface
            # - Each package has to be sent in a separate request
            # - First package is called "master" package and holds shipping-
            #   related information, including addresses, customs...
            # - Last package responses contains shipping price and code
            # - If a problem happens with a package, every previous package
            #   of the shipping has to be cancelled separately
            # (Why doing it in a simple way when the complex way exists??)

            master_tracking_id = False
            package_labels = []
            carrier_tracking_ref = ""

            for sequence in range(1, package_count + 1):
                package_weight = _convert_weight(popup.weight, self.fedex_weight_unit)
                srm.add_package(package_weight, sequence_number=sequence)
                _add_customer_references(srm, order)
                srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                request = srm.process_shipment()
                package_name = sequence

                warnings = request.get('warnings_message')
                if warnings:
                    _logger.info(warnings)

                # First package
                if sequence == 1:
                    if not request.get('errors_message'):
                        master_tracking_id = request['master_tracking_id']
                        package_labels.append((package_name, srm.get_label()))
                        carrier_tracking_ref = request['tracking_number']
                        print("first")
                        print(carrier_tracking_ref)
                    else:
                        raise UserError(request['errors_message'])

                # Intermediary packages
                elif sequence > 1 and sequence < package_count:
                    if not request.get('errors_message'):
                        package_labels.append((package_name, srm.get_label()))
                        carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        print("Intermediary packages")
                        print(carrier_tracking_ref)
                    else:
                        raise UserError(request['errors_message'])

                # Last package
                elif sequence == package_count:
                    # recuperer le label pdf
                    if not request.get('errors_message'):
                        package_labels.append((package_name, srm.get_label()))

                        if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                            carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                        else:
                            _logger.info("Preferred currency has not been found in FedEx response")
                            company_currency = order.company_id.currency_id
                            if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                carrier_price = company_currency.compute(
                                    request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                            else:
                                carrier_price = company_currency.compute(request['price']['USD'], order_currency)

                        carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        order.update({
                            'carrier_id': self,
                            'shipping_number': carrier_tracking_ref.replace(request['master_tracking_id'], request['master_tracking_id']+'*')
                        })

                        logmessage = _("Shipment created into Fedex<br/>"
                                       "<b>Tracking Numbers:</b> %s<br/>"
                                       "<b>Packages:</b> %s") % (
                                         carrier_tracking_ref, ','.join([str(pl[0]) for pl in package_labels]))
                        if self.fedex_label_file_type != 'PDF':
                            attachments = [('FedEx_Label-%s-%s.%s' % (self.fedex_service_type,order.name, self.fedex_label_file_type), pl[1]) for pl in
                                           package_labels]
                        if self.fedex_label_file_type == 'PDF':
                            attachments = [('FedEx_Label-%s-%s.%s' % (self.fedex_service_type,order.name, self.fedex_label_file_type), pdf.merge_pdf([pl[1] for pl in package_labels]))]
                        order.message_post(body=logmessage, attachments=attachments)
                        shipping_data = {'exact_price': carrier_price,
                                         'tracking_number': carrier_tracking_ref}
                        res = res + [shipping_data]
                        print("Last package")
                        print(carrier_tracking_ref)
                    else:
                        raise UserError(request['errors_message'])

        # TODO RIM handle if a package is not accepted (others should be deleted)

        ###############
        # One package #
        ###############
        elif package_count == 1:

            srm.add_package(net_weight)
            srm.set_master_package(net_weight, 1)
            _add_customer_references(srm, order)

            # Ask the shipping to fedex
            request = srm.process_shipment()

            warnings = request.get('warnings_message')
            if warnings:
                _logger.info(warnings)

            if not request.get('errors_message'):

                if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                    carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                else:
                    _logger.info("Preferred currency has not been found in FedEx response")
                    company_currency = order.company_id.currency_id
                    if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                        carrier_price = company_currency.compute(
                            request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                    else:
                        carrier_price = company_currency.compute(request['price']['USD'], order_currency)

                carrier_tracking_ref = request['tracking_number']
                order.update({
                    'carrier_id': self,
                    'shipping_number': carrier_tracking_ref
                })
                logmessage = (
                        _("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))

                fedex_labels = [
                    ('FedEx_Label-%s-%s-%s.%s' % (self.fedex_service_type,order.name, index, self.fedex_label_file_type), label)
                    for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                order.message_post(body=logmessage, attachments=fedex_labels)

                shipping_data = {'exact_price': carrier_price,
                                 'tracking_number': carrier_tracking_ref}
                res = res + [shipping_data]
            else:
                raise UserError(request['errors_message'])

        ##############
        # No package #
        ##############
        else:
            raise UserError(_('Please provide packages count'))
        return res

        # // Below method is override for sales order fedex shipping Label PO

    # TODO
    """
        UPG_ODOO16_NOTE: 
        # below method "fedex_send_shipping" is odoo core method and we overrided it but have to comment it beacuse causing error 
                
    """

    #@api.multi
    # def fedex_send_shipping(self, pickings):
    #     _logger.info('Override fedex_send_shipping method call')
    #     res = []
    #
    #     for picking in pickings:
    #
    #         srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
    #         superself = self.sudo()
    #         srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
    #         srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)
    #
    #         srm.transaction_detail(picking.id)
    #
    #         package_type = picking.package_ids and picking.package_ids[
    #             0].packaging_id.package_type_id.shipper_package_code or self.fedex_default_package_type_id.shipper_package_code
    #         srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type,
    #                              self.fedex_weight_unit, self.fedex_saturday_delivery)
    #         srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
    #         srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id)
    #         srm.set_recipient(picking.partner_id)
    #
    #         srm.shipping_charges_payment(superself.fedex_account_number)
    #
    #         srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type,
    #                            'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')
    #
    #         order = picking.sale_id
    #         company = order.company_id or picking.company_id or self.env.user.company_id
    #         order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
    #
    #         net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit)
    #
    #         # Commodities for customs declaration (international shipping)
    #         if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (
    #                 picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):
    #
    #             commodity_currency = order_currency
    #             total_commodities_amount = 0.0
    #             commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code
    #
    #             for operation in picking.move_line_ids:
    #                 commodity_amount = operation.move_id.sale_line_id.price_unit or operation.product_id.list_price
    #                 total_commodities_amount += (commodity_amount * operation.qty_done)
    #                 commodity_description = operation.product_id.name
    #                 commodity_number_of_piece = '1'
    #                 commodity_weight_units = self.fedex_weight_unit
    #                 commodity_weight_value = self._fedex_convert_weight(
    #                     operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
    #                 commodity_quantity = operation.qty_done
    #                 commodity_quantity_units = 'EA'
    #                 # DO NOT FORWARD PORT AFTER 12.0
    #                 if getattr(operation.product_id, 'hs_code', False):
    #                     commodity_harmonized_code = operation.product_id.hs_code or ''
    #                 else:
    #                     commodity_harmonized_code = ''
    #                 srm._commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount,
    #                                  commodity_number_of_piece, commodity_weight_units, commodity_weight_value,
    #                                  commodity_description, commodity_country_of_manufacture, commodity_quantity,
    #                                  commodity_quantity_units, commodity_harmonized_code)
    #             srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount,
    #                               "NON_DOCUMENTS")
    #             srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id.country_id.code,
    #                                superself.fedex_account_number)
    #
    #         package_count = len(picking.package_ids) or 1
    #
    #         # For india picking courier is not accepted without this details in label.
    #         po_number = dept_number = False
    #         if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
    #             po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
    #             dept_number = 'BILL D/T: SENDER'
    #
    #         # TODO RIM master: factorize the following crap
    #
    #         ################
    #         # Multipackage #
    #         ################
    #         if package_count > 1:
    #
    #             # Note: Fedex has a complex multi-piece shipping interface
    #             # - Each package has to be sent in a separate request
    #             # - First package is called "master" package and holds shipping-
    #             #   related information, including addresses, customs...
    #             # - Last package responses contains shipping price and code
    #             # - If a problem happens with a package, every previous package
    #             #   of the shipping has to be cancelled separately
    #             # (Why doing it in a simple way when the complex way exists??)
    #
    #             master_tracking_id = False
    #             package_labels = []
    #             carrier_tracking_ref = ""
    #
    #             for sequence, package in enumerate(picking.package_ids, start=1):
    #
    #                 package_weight = self._fedex_convert_weight(package.shipping_weight, self.fedex_weight_unit)
    #                 packaging = package.packaging_id
    #                 _add_customer_references_so(srm, order)
    #                 srm._add_package(
    #                     package_weight,
    #                     package_code=packaging.package_type_id.shipper_package_code,
    #                     package_height=packaging.package_type_id.height,
    #                     package_width=packaging.package_type_id.width,
    #                     package_length=packaging.package_type_id.length,
    #                     sequence_number=sequence,
    #                     po_number=po_number,
    #                     dept_number=dept_number,
    #                 )
    #                 srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
    #                 request = srm.process_shipment()
    #                 package_name = package.name or sequence
    #
    #                 warnings = request.get('warnings_message')
    #                 if warnings:
    #                     _logger.info(warnings)
    #
    #                 # First package
    #                 if sequence == 1:
    #                     if not request.get('errors_message'):
    #                         master_tracking_id = request['master_tracking_id']
    #                         package_labels.append((package_name, srm.get_label()))
    #                         carrier_tracking_ref = request['tracking_number']
    #                     else:
    #                         raise UserError(request['errors_message'])
    #
    #                 # Intermediary packages
    #                 elif sequence > 1 and sequence < package_count:
    #                     if not request.get('errors_message'):
    #                         package_labels.append((package_name, srm.get_label()))
    #                         carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
    #                     else:
    #                         raise UserError(request['errors_message'])
    #
    #                 # Last package
    #                 elif sequence == package_count:
    #                     # recuperer le label pdf
    #                     if not request.get('errors_message'):
    #                         package_labels.append((package_name, srm.get_label()))
    #
    #                         if _convert_curr_iso_fdx(order_currency.name) in request['price']:
    #                             carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
    #                         else:
    #                             _logger.info("Preferred currency has not been found in FedEx response")
    #                             company_currency = picking.company_id.currency_id
    #                             if _convert_curr_iso_fdx(company_currency.name) in request['price']:
    #                                 amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
    #                                 carrier_price = company_currency._convert(
    #                                     amount, order_currency, company, order.date_order or fields.Date.today())
    #                             else:
    #                                 amount = request['price']['USD']
    #                                 carrier_price = company_currency._convert(
    #                                     amount, order_currency, company, order.date_order or fields.Date.today())
    #
    #                         carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
    #
    #                         logmessage = _("Shipment created into Fedex<br/>"
    #                                        "<b>Tracking Numbers:</b> %s<br/>"
    #                                        "<b>Packages:</b> %s") % (
    #                                          carrier_tracking_ref, ','.join([pl[0] for pl in package_labels]))
    #                         if self.fedex_label_file_type != 'PDF':
    #                             attachments = [('LabelFedex-%s.%s' % (pl[0], self.fedex_label_file_type), pl[1]) for
    #                                            pl in package_labels]
    #                         if self.fedex_label_file_type == 'PDF':
    #                             attachments = [('LabelFedex.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
    #                         picking.message_post(body=logmessage, attachments=attachments)
    #                         shipping_data = {'exact_price': carrier_price,
    #                                          'tracking_number': carrier_tracking_ref}
    #                         res = res + [shipping_data]
    #                     else:
    #                         raise UserError(request['errors_message'])
    #
    #         # TODO RIM handle if a package is not accepted (others should be deleted)
    #
    #         ###############
    #         # One package #
    #         ###############
    #         elif package_count == 1:
    #             srm.add_package(net_weight)
    #             _add_customer_references_so(srm, order)
    #
    #             # packaging = picking.package_ids[:1].packaging_id or picking.carrier_id.fedex_default_package_type_id
    #             # srm._add_package(
    #             #     net_weight,
    #             #     package_code=packaging.package_type_id.shipper_package_code,
    #             #     package_height=packaging.package_type_id.height,
    #             #     package_width=packaging.package_type_id.width,
    #             #     package_length=packaging.package_type_id.length,
    #             #     po_number=po_number,
    #             #     dept_number=dept_number,
    #             # )
    #             srm.set_master_package(net_weight, 1)
    #
    #             # Ask the shipping to fedex
    #             request = srm.process_shipment()
    #
    #             warnings = request.get('warnings_message')
    #             if warnings:
    #                 _logger.info(warnings)
    #
    #             if not request.get('errors_message'):
    #
    #                 if _convert_curr_iso_fdx(order_currency.name) in request['price']:
    #                     carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
    #                 else:
    #                     _logger.info("Preferred currency has not been found in FedEx response")
    #                     company_currency = picking.company_id.currency_id
    #                     if _convert_curr_iso_fdx(company_currency.name) in request['price']:
    #                         amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
    #                         carrier_price = company_currency._convert(
    #                             amount, order_currency, company, order.date_order or fields.Date.today())
    #                     else:
    #                         amount = request['price']['USD']
    #                         carrier_price = company_currency._convert(
    #                             amount, order_currency, company, order.date_order or fields.Date.today())
    #
    #                 carrier_tracking_ref = request['tracking_number']
    #                 logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (
    #                     carrier_tracking_ref))
    #
    #                 fedex_labels = [
    #                     ('LabelFedex-%s-%s.%s' % (carrier_tracking_ref, index, self.fedex_label_file_type), label)
    #                     for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
    #                 picking.message_post(body=logmessage, attachments=fedex_labels)
    #
    #                 shipping_data = {'exact_price': carrier_price,
    #                                  'tracking_number': carrier_tracking_ref}
    #                 res = res + [shipping_data]
    #             else:
    #                 raise UserError(request['errors_message'])
    #
    #         ##############
    #         # No package #
    #         ##############
    #         else:
    #             raise UserError(('No packages for this picking'))
    #
    #     return res



def _convert_weight(weight, unit='KG'):
    ''' Convert picking weight (always expressed in KG) into the specified unit '''
    if unit == 'KG':
        return weight
    elif unit == 'LB':
        return weight / 0.45359237
    else:
        raise ValueError


def _add_customer_references(srm, order):
    srm.customer_references('P_O_NUMBER', order.name)
    if order.acq_user_id.id:
        srm.customer_references('CUSTOMER_REFERENCE', order.acq_user_id.name)

 # Method added for setting value to PO for shipping label in sales order
def _add_customer_references_so(srm, order):
    if order.client_order_ref:
        srm.customer_references('P_O_NUMBER', order.client_order_ref)


def _convert_curr_iso_fdx(code):
    return FEDEX_CURR_MATCH.get(code, code)


