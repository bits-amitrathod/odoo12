# -*- coding: utf-8 -*-
import logging
import time

from docutils.nodes import reference
from zeep.helpers import serialize_object

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError
from odoo.tools import pdf, float_repr
from .fedex_request import FedexRequest as CustomFedexRequest
from odoo.addons.delivery_fedex.models.fedex_request import FedexRequest


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
        srm = CustomFedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
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

    def fedex_send_shipping(self, pickings):
        res = []

        for picking in pickings:
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id

            srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            srm.transaction_detail(picking.id)

            package_type = picking.package_ids and picking.package_ids[0].package_type_id.shipper_package_code or self.fedex_default_package_type_id.shipper_package_code
            srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit, self.fedex_saturday_delivery)
            srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
            srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id)
            srm.set_recipient(picking.partner_id)

            srm.shipping_charges_payment(superself.fedex_account_number)

            srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')

            order = picking.sale_id

            net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit)

            # Commodities for customs declaration (international shipping)
            if 'INTERNATIONAL' in self.fedex_service_type  or (picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):

                commodities = self._get_commodities_from_stock_move_lines(picking.move_line_ids)
                for commodity in commodities:
                    srm.commodities(self, commodity, _convert_curr_iso_fdx(order_currency.name))

                total_commodities_amount = sum(c.monetary_value * c.qty for c in commodities)
                srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
                srm.duties_payment(order.warehouse_id.partner_id, superself.fedex_account_number, superself.fedex_duty_payment)

                send_etd = superself.env['ir.config_parameter'].get_param("delivery_fedex.send_etd")
                srm.commercial_invoice(self.fedex_document_stock_type, send_etd)

            package_count = len(picking.package_ids) or 1

            # For india picking courier is not accepted without this details in label.
            po_number = order.display_name or False
            dept_number = False
            """........BITS......No need of dept_number in the label that's why commenting the below code..........."""
            # if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
            #     po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
            #     dept_number = 'BILL D/T: SENDER'

            # TODO RIM master: factorize the following crap

            packages = self._get_packages_from_picking(picking, self.fedex_default_package_type_id)

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
            carrier_tracking_refs = []
            lognote_pickings = picking.sale_id.picking_ids if picking.sale_id else picking

            """...........BITS....No need of reference that's why commenting the below code.................... """
            # reference = picking.display_name
            reference = False

            for sequence, package in enumerate(packages, start=1):

                srm.add_package(
                    self,
                    package,
                    _convert_curr_iso_fdx(package.company_id.currency_id.name),
                    sequence_number=sequence,
                    po_number=po_number,
                    dept_number=dept_number,
                    reference=reference,
                )
                srm.set_master_package(net_weight, len(packages), master_tracking_id=master_tracking_id)

                # Prepare the request
                self._fedex_update_srm(srm, 'ship', picking=picking)
                request = serialize_object(dict(WebAuthenticationDetail=srm.WebAuthenticationDetail,
                                                ClientDetail=srm.ClientDetail,
                                                TransactionDetail=srm.TransactionDetail,
                                                VersionId=srm.VersionId,
                                                RequestedShipment=srm.RequestedShipment))
                self._fedex_add_extra_data_to_request(request, 'ship')
                response = srm.process_shipment(request)

                warnings = response.get('warnings_message')
                if warnings:
                    _logger.info(warnings)

                if response.get('errors_message'):
                    raise UserError(response['errors_message'])

                package_name = package.name or 'package-' + str(sequence)
                package_labels.append((package_name, srm.get_label()))
                carrier_tracking_refs.append(response['tracking_number'])
                carrier_tracking_ref = response['tracking_number'] or ''

                # First package
                if sequence == 1:
                    master_tracking_id = response['master_tracking_id']

                # Last package
                if sequence == package_count:

                    carrier_price = self._get_request_price(response['price'], order, order_currency)

                    logmessage = _("Shipment created into Fedex<br/>"
                                   "<b>Tracking Numbers:</b> %s<br/>"
                                   "<b>Packages:</b> %s") % (','.join(carrier_tracking_refs), ','.join([pl[0] for pl in package_labels]))
                    if self.fedex_label_file_type != 'PDF':
                        attachments = [('LabelFedex-%s-%s.%s' % (pl[0], str(carrier_tracking_ref), self.fedex_label_file_type), pl[1]) for pl in package_labels]
                    if self.fedex_label_file_type == 'PDF':
                        attachments = [('LabelFedex-%s-%s.pdf' % (str(carrier_tracking_ref),str(sequence)), pdf.merge_pdf([pl[1] for pl in package_labels]))]
                    for pick in lognote_pickings:
                        pick.message_post(body=logmessage, attachments=attachments)
                    shipping_data = {'exact_price': carrier_price,
                                     'tracking_number': ','.join(carrier_tracking_refs)}
                    res = res + [shipping_data]

            # TODO RIM handle if a package is not accepted (others should be deleted)

            if self.return_label_on_delivery:
                self.get_return_label(picking, tracking_number=response['tracking_number'], origin_date=response['date'])
            commercial_invoice = srm.get_document()
            if commercial_invoice:
                fedex_documents = [('DocumentFedex.pdf', commercial_invoice)]
                for pick in lognote_pickings:
                    pick.message_post(body='Fedex Documents', attachments=fedex_documents)
        return res


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


