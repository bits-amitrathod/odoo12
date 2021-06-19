# -*- coding: utf-8 -*-
import os
from datetime import datetime

from odoo import models, api, fields
from zeep import Client, Plugin, Settings
from zeep.exceptions import Fault
from zeep.wsdl.utils import etree_to_string
from odoo.tools import remove_accents

class LogPlugin(Plugin):
    """ Small plugin for suds that catches out/ingoing XML requests and logs them"""

    def __init__(self, debug_logger):
        self.debug_logger = debug_logger

    def egress(self, envelope, http_headers, operation, binding_options):
        self.debug_logger(etree_to_string(envelope).decode(), 'fedex_request')
        return envelope, http_headers

    def ingress(self, envelope, http_headers, operation):
        self.debug_logger(etree_to_string(envelope).decode(), 'fedex_response')
        return envelope, http_headers


class FedexApiCstm():

    def __init__(self, debug_logger, prod_environment=False):
        # super().__init__(debug_logger, prod_environment)
        self.debug_logger = debug_logger
        self.hasCommodities = False
        self.hasOnePackage = False

        env_path = '../api/test/'
        if prod_environment:
            env_path = '../api/prod/'
        wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), env_path + 'TrackService_v16.wsdl')
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'), plugins=[LogPlugin(self.debug_logger)])
        self.factory = self.client.type_factory('ns0')

    def set_version(self, serviceId, major, intermediate, minor):
        self.Version = self.factory.VersionId()
        self.Version.ServiceId = serviceId
        self.Version.Major = major
        self.Version.Intermediate = intermediate
        self.Version.Minor = minor

    def set_tracking_umber(self, trackingNumber):
        self.selectionDetails = self.factory.TrackSelectionDetail()
        self.selectionDetails.PackageIdentifier = self.factory.TrackPackageIdentifier()
        self.selectionDetails.PackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
        self.selectionDetails.PackageIdentifier.Value = trackingNumber
        # delattr(self.selectionDetails, 'OperatingCompany')
        # delattr(self.selectionDetails, 'CarrierCode')
        # delattr('OperatingCompany', self.selectionDetails)
        # delattr('CarrierCode', self.selectionDetails)

    def process_track_request(self):

        formatted_response = {}

        try:
            self.response = self.client.service.track(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                      ClientDetail=self.ClientDetail,
                                                      Version=self.Version,
                                                      SelectionDetails=self.selectionDetails)

            if self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE' and \
                    self.response.CompletedTrackDetails[0].TrackDetails[0].Notification.Severity != 'ERROR':
                trackDetails = self.response.CompletedTrackDetails[0].TrackDetails[0]
                if 'Events' in trackDetails:
                    event = trackDetails.Events[0]
                    formatted_response['data'] = '<dl class="dl-horizontal"> <dt>Tracking Number</dt><dd>' + \
                                                 trackDetails.TrackingNumber + "</dd>" \
                                                                               "<dt>Status</dt> <dd>" + event.EventDescription + "</dd>" \
                                                                                                                                 "<dt>Event Date</dt> <dd>" + event.Timestamp.strftime(
                        "%m/%d/%Y %I:%M:%S %p") + "</dd>"

                    isMaster = False
                    isMasterFound = False

                    if 'OtherIdentifiers' in trackDetails:
                        otherIdentifiers = trackDetails.OtherIdentifiers
                        for otherIdentifier in otherIdentifiers:
                            if otherIdentifier.PackageIdentifier.Type == 'STANDARD_MPS':
                                isMasterFound = True
                                if otherIdentifier.PackageIdentifier.Value == str(
                                        self.selectionDetails.PackageIdentifier.Value):
                                    isMaster = True
                                    break

                        if not isMasterFound:
                            isMaster = True
                    else:
                        isMaster = True

                    datesOrTimes = trackDetails.DatesOrTimes
                    isExpectedDate = False
                    if isMaster:
                        for track in datesOrTimes:
                            if track.Type == 'ESTIMATED_DELIVERY':
                                formatted_response['expected_date'] = track.DateOrTimestamp[
                                                                      0:track.DateOrTimestamp.find('T')]
                                isExpectedDate = datetime.strptime(str(formatted_response['expected_date']),
                                                                   "%Y-%m-%d").strftime("%m/%d/%Y")

                            if track.Type == 'ACTUAL_DELIVERY':
                                formatted_response['delivered_date'] = track.DateOrTimestamp[
                                                                       0:track.DateOrTimestamp.find('T')]

                            if track.Type == 'SHIP':
                                formatted_response['shipping_date'] = track.DateOrTimestamp[
                                                                      0:track.DateOrTimestamp.find('T')]
                    address = ""
                    if event.Address:
                        address += event.Address.Residential + "<br/>" if 'Residential' in event.Address and event.Address.Residential else ""
                        address += event.Address.City + "<br/>" if 'City' in event.Address and event.Address.City else ""
                        address += event.Address.StateOrProvinceCode + "<br/>" if 'StateOrProvinceCode' in event.Address and event.Address.StateOrProvinceCode else ""
                        address += event.Address.CountryName + "<br/>" if 'CountryName' in event.Address and event.Address.CountryName else ""
                        address += event.Address.PostalCode + "<br/>" if 'PostalCode' in event.Address and event.Address.PostalCode else ""
                    else:
                        address = "N/A"
                    formatted_response['data'] += "<dt>Current Location</dt><dd>" + address + "</dd>"

                    if isExpectedDate:
                        formatted_response['data'] += "<dt> Expected / Estimated Delivery </dt><dd>" + str(
                            isExpectedDate) + "</dd>"

                    formatted_response['data'] += "</dl>"

                else:
                    formatted_response['data'] = "Tracking data not available"


            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if
                                            (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                if errors_message == '':
                    errors_message = "Please try again later."
                    if self.response.CompletedTrackDetails[0].TrackDetails[0].Notification.Severity == 'ERROR':
                        errors_message = self.response.CompletedTrackDetails[0].TrackDetails[0].Notification.Message
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join(
                    [("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except Fault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"

        return formatted_response

    def web_authentication_detail(self, key, password):
        WebAuthenticationCredential = self.factory.WebAuthenticationCredential()
        WebAuthenticationCredential.Key = key
        WebAuthenticationCredential.Password = password
        self.WebAuthenticationDetail = self.factory.WebAuthenticationDetail()
        self.WebAuthenticationDetail.UserCredential = WebAuthenticationCredential

    def client_detail(self, account_number, meter_number):
        self.ClientDetail = self.factory.ClientDetail()
        self.ClientDetail.AccountNumber = account_number
        self.ClientDetail.MeterNumber = meter_number


class FedexDelivery(models.Model):
    _inherit = 'delivery.carrier'

    def get_tracking(self, order, tracking_numbers):
        view = self.env.ref('fedex_api_cstm.tracing_number_popup')
        context = dict(self._context or {})
        context['carrier'] = order.carrier_id.id
        context['isFedEx'] = order.carrier_id.delivery_type == 'fedex'
        if order._name == 'purchase.order':
            context['purchase_order'] = order.id
        else:
            context['purchase_order'] = False

        if len(tracking_numbers) > 1:
            context['tracking_numbers'] = []
            for tracking_number in tracking_numbers:
                context['tracking_numbers'].append((str(tracking_number).replace('*', ''), tracking_number))
            return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": 'tracking.popup',
                "name": "Track Shipment",
                'views': [(view.id, 'form')],
                'target': 'new',
                'domain': [],
                'context': context,
            }
        else:
            # [787779905397, 787779905765, 787779906750]
            return self.fedex_track_request(order, tracking_numbers)

    def fedex_track_request(self, order, tracking_numbers):
        # self.prod_environment
        message = ""
        for tracking_number in tracking_numbers:

            # self.prod_environment
            srm = FedexApiCstm(self.log_xml, prod_environment=self.prod_environment)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            # srm.web_authentication_detail('hFceAv3XJUumwZaS', 'jQDWagVknWD3OZIe3jn9vdtab')
            # srm.client_detail(339923531, 114470940)

            srm.set_version('trck', 16, 0, 0)
            srm.set_tracking_umber(tracking_number)
            logmessage = srm.process_track_request()
            # str(tracking_number) + ": " +
            if 'data' in logmessage:
                message += logmessage['data']
            else:
                message += logmessage['errors_message'] + "<br/>"

            if order._name == 'purchase.order':
                message += '<div class="well well-sm">Note: This status will be saved under "Deliveries & Invoices" section of this PO#</div>'
                if 'expected_date' in logmessage:
                    order.expected_date = logmessage['expected_date']

                if 'delivered_date' in logmessage:
                    order.delivered_date = logmessage['delivered_date']

                if 'shipping_date' in logmessage:
                    order.shipping_date = logmessage['shipping_date']

        if message:
            view = self.env.ref('fedex_api_cstm.cstm_popup_message')
            context = dict(self._context or {})
            context['message'] = message
            return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": 'cstm.popup.message',
                "name": "Track Shipment",
                'views': [(view.id, 'form')],
                'target': 'new',
                'domain': [],
                'context': context,
            }


class cstm_popup_message(models.TransientModel):
    _name = "cstm.popup.message"

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Html(string="Message", readonly=True, default=get_default)


class tracking_popup(models.TransientModel):
    _name = "tracking.popup"

    def get_default(self):
        if self.env.context.get("tracking_numbers", False):
            return self.env.context.get("tracking_numbers")
        return False

    def get_default_carrier(self):
        if self.env.context.get("carrier", False):
            return self.env.context.get("carrier")
        return False

    def get_default_purchase_order(self):
        if self.env.context.get("purchase_order", False):
            return self.env.context.get("purchase_order")
        return False

    tracking_number = fields.Selection(get_default, string="Tracking Number", required=True)
    carrier_id = fields.Many2one('delivery.carrier', 'Carrier', readonly=True, default=get_default_carrier)
    order_id = fields.Many2one('purchase.order', string='Purchase Order#', default=get_default_purchase_order)

    def open_table(self):
        if self.env.context['purchase_order']:
            order = self.order_id
        else:
            order = self
        return self.carrier_id.fedex_track_request(order, [int(self.tracking_number)])

    #@api.multi
    def track_fedex(self):
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "act_url",
            'target': 'new',
            'url': "https://fedex.com/apps/fedextrack/?action=track&trackingnumber=%s" % str(self.tracking_number),
        }
        return client_action


class VendorOfferTrack(models.Model):
    _inherit = "purchase.order"

    #@api.multi
    def action_fedex_track_request(self):
        if self.carrier_id:
            return self.carrier_id.get_tracking(self, self.shipping_number.split(","))


class sale_order_track(models.Model):
    _inherit = 'sale.order'

    #@api.multi
    def action_fedex_track_request(self):
        if self.carrier_id:
            return self.carrier_id.get_tracking(self, [self.carrier_track_ref])

class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_tracking_url = fields.Char(string='Tracking URL', compute='_compute_carrier_tracking_url')

    @api.depends('carrier_id', 'carrier_tracking_ref')
    def _compute_carrier_tracking_url(self):
        for picking in self:
            result = picking.carrier_id.get_tracking_link(picking) if picking.carrier_id and picking.carrier_tracking_ref else False
            picking.carrier_tracking_url = result if result else ""

