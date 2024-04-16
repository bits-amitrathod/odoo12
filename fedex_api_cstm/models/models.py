# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta
import requests, json, logging
from odoo import models, api, fields,tools
from odoo.exceptions import Warning, UserError,ValidationError

logger = logging.getLogger(__name__)


class FedexRestApi:

    """ Low-level object intended to interface Odoo recordsets with FedEx,
        through appropriate REST requests """

    def __init__(self, request_type="tracking", prod_environment=False):
        self.oauth_token = ""
        if request_type == "tracking":
            if prod_environment:
                self.api_end_point = 'https://apis.fedex.com'
            else:
                self.api_end_point = 'https://apis-sandbox.fedex.com'
                #self.api_end_point = 'https://apis.fedex.com'

    def generate_authentication_token(self, apikey, secret):
        url = self.api_end_point + "/oauth/token"
        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }
        payload = {
            "client_id": apikey,
            "client_secret": secret,
            "grant_type": "client_credentials"
        }
        response = requests.post(url, data=payload, headers=headers)
        self.validate_response(response)
        self.oauth_token = response.json()["access_token"]
        return self.oauth_token

    def validate_response(self,response):
        if response.status_code == 200:
            return True
        else:
            response = response.json()
            error_code = ""
            error_message = "Something went wrong please contact your Admin"
            if 'error' in response:
                error_code = response["error"]
                error_message = response['error_description']
            if 'errors' in response:
                error_code = response["errors"][0]['code']
                error_message = response["errors"][0]['message']

            error_msg = f"{error_code} {error_message}"
            logger.info("\n\n FEDEX API response " + error_msg)
            raise ValidationError(error_msg)

    def process_track_request(self, response):

        formatted_response = {}
        output = 'output' in response and response['output']
        alerts = output.get('alerts', '')
        completeTrackResults = output and output.get('completeTrackResults', False)
        trackResults = completeTrackResults and completeTrackResults[0]['trackResults'][0]
        trackingNumber = completeTrackResults and completeTrackResults[0]['trackingNumber'] or ""
        formatted_response['data'] = ''
        if alerts and False:
            formatted_response['alerts'] = alerts
            formatted_response['data'] = ''
            for alert in alerts:
                formatted_response['data'] += "<br/>" + '<dl class="dl-horizontal"> <dt>Alert Type</dt><dd>' + alert.get('alertType','') + "</dd>" \
                                                "<dt>Message</dt> <dd>" + alert.get('message','') + "</dd>"

        if 'scanEvents' in trackResults:
            event = trackResults['scanEvents'][0]
            strEventDate = event.get('date','')[0:event.get('date', '').find('T')]
            eventDate = str(datetime.strptime(str(strEventDate), "%Y-%m-%d").strftime(tools.misc.DEFAULT_SERVER_DATE_FORMAT))
            formatted_response['data'] = '<dl class="dl-horizontal"> <dt>Tracking Number</dt><dd>' + \
                                            trackingNumber + "</dd>" \
                                        "<dt>Event Status</dt> <dd>" + event.get('eventDescription','') + "</dd>" \
                                        "<dt>Event Date</dt> <dd>" + eventDate + "</dd>"

            isMaster = True
            isMasterFound = False
            additionalTrackingInfo = 'additionalTrackingInfo' in trackResults and trackResults['additionalTrackingInfo']
            if additionalTrackingInfo:
                packageIdentifiers = additionalTrackingInfo['packageIdentifiers']
                for identifier in packageIdentifiers:
                    if identifier.get('type') == 'STANDARD_MPS':
                        isMasterFound = True
                    # if identifier.get('value') == str(self.selectionDetails.PackageIdentifier.Value):
                    #     isMaster = True
                    #     break



            datesOrTimes = trackResults.get('dateAndTimes',False)
            isExpectedDate = False
            if isMaster and datesOrTimes:
                for track in datesOrTimes:
                    dateTime = track.get('dateTime', '')[0:track.get('dateTime', '').find('T')]
                    if track.get('type') == 'ESTIMATED_DELIVERY':
                        formatted_response['expected_date'] = dateTime
                        isExpectedDate = datetime.strptime(str(dateTime),"%Y-%m-%d").strftime(tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)

                    if track.get('type') == 'ACTUAL_DELIVERY':
                        formatted_response['delivered_date'] = dateTime

                    if track.get('type') == 'SHIP':
                        formatted_response['shipping_date'] = dateTime

                scanLocation = event.get('scanLocation',False)
                if scanLocation:
                    address = ""
                    address += scanLocation.get('residential',False) + "<br/>" if scanLocation.get('residential',False) else ""
                    address += scanLocation.get('city',False) + "<br/>" if scanLocation.get('city',False) else ""
                    address += scanLocation.get('stateOrProvinceCode',False) + "<br/>" if scanLocation.get('stateOrProvinceCode',False) else ""
                    address += scanLocation.get('countryName',False) + "<br/>" if scanLocation.get('countryName',False) else ""
                    address += scanLocation.get('postalCode',False) + "<br/>" if scanLocation.get('postalCode',False) else ""
                else:
                    address = "N/A"

                formatted_response['data'] += "<dt>Current Location</dt><dd>" + address + "</dd>"

                if isExpectedDate:
                    formatted_response['data'] += "<dt> Expected / Estimated Delivery </dt><dd>" + str(isExpectedDate) + "</dd>"
                else:
                    estimatedDeliveryTimeWindow = trackResults.get('estimatedDeliveryTimeWindow',False)
                    type = estimatedDeliveryTimeWindow and estimatedDeliveryTimeWindow.get('type') == 'ESTIMATED_DELIVERY'
                    dateBegins = type and estimatedDeliveryTimeWindow['window']['begins'][0:estimatedDeliveryTimeWindow['window']['begins'].find('T')] or ''
                    dateEnd = type and estimatedDeliveryTimeWindow['window']['ends'][0:estimatedDeliveryTimeWindow['window']['ends'].find('T')] or ''
                    if dateBegins and dateEnd:
                        expactedDateBegin = datetime.strptime(str(dateBegins),"%Y-%m-%d").strftime(tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
                        expactedDateEnd = datetime.strptime(str(dateEnd),"%Y-%m-%d").strftime(tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
                        formatted_response['expected_date'] = expactedDateEnd or False
                        formatted_response['data'] += "<dt> Expected / Estimated Delivery Window </dt><dd>" + str(expactedDateBegin) + "to " + str(expactedDateEnd) +"</dd>"

                formatted_response['data'] += "</dl>"

        errors = response.get('errors')
        if errors:
            formatted_response['errors_message'] = '\n'.join([("%s: %s" % (error.code, error.error_message)) for error in errors])

        return formatted_response

    def process_tracking_request(self, tracking_num):
        url = self.api_end_point + "/track/v1/trackingnumbers"
        headers = {
            "content-type": "application/json",
            "Authorization": "Bearer " + self.oauth_token
        }
        payload = {
                "includeDetailedScans": True,
                "trackingInfo": [
                    {
                    "trackingNumberInfo": {
                        "trackingNumber": tracking_num
                        }
                    }
                ]
            }
        response = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
        self.validate_response(response)
        return self.process_track_request(response.json())


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

    def get_fedex_token(self):
        #is_production_env = self.env['ir.config_parameter'].sudo().get_param('fedex_api_cstm.is_production_env')
        #is_production_env = self.prod_environment
        secret_key = self.env['ir.config_parameter'].sudo().get_param('fedex_api_cstm.project_secret_key')
        api_key = self.env['ir.config_parameter'].sudo().get_param('fedex_api_cstm.fedex_api_key')
        fedex_token = self.env['ir.config_parameter'].sudo().get_param('fedex.api_request_token')
        oauth_token = False
        # oauth_token = ''
        if not secret_key or not api_key:
            raise ValidationError("Fedex Api credentials is missing in System parameter please check and request again")

        if fedex_token:
            token_time = f"{fedex_token.split()[1]} {fedex_token.split()[2]}"
            token_time = datetime.strptime(token_time, tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
            oauth_token = token_time > datetime.now() and fedex_token.split()[0]

        if not oauth_token:
            fedex = FedexRestApi(prod_environment=self.prod_environment)
            oauth_token = fedex.generate_authentication_token(api_key, secret_key)
            token_exp_on = (datetime.now() + timedelta(hours=1)).strftime(tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
            self.env["ir.config_parameter"].sudo().set_param("fedex.api_request_token", oauth_token + "  " + token_exp_on)
            self.env.cr.commit()
        if not oauth_token:
            raise ValidationError("Unable to get Fedex Authentication Token for API request, "
                                  "please check your credentials.")
        return oauth_token

    def fedex_track_request(self, order, tracking_numbers):
        # self.prod_environment

        message = ""
        for tracking_number in tracking_numbers:
            #is_production_env = self.env['ir.config_parameter'].sudo().get_param('fedex_api_cstm.is_production_env')
            #is_production_env = self.prod_environment
            fedex = FedexRestApi(prod_environment=self.prod_enviourment)
            fedex.oauth_token = self.get_fedex_token()
            formatted_response = fedex.process_tracking_request(tracking_number)
            message += formatted_response.get('data','')
            if 'alerts' not in formatted_response and 'errors_message' not in formatted_response:
                if order._name == 'purchase.order':
                    message += '<div class="well well-sm">Note: This status will be saved ' \
                               'under "Deliveries & Invoices" section of this PO#</div>'
                    if 'expected_date' in formatted_response:
                        order.expected_date = formatted_response['expected_date']

                    if 'delivered_date' in formatted_response:
                        order.delivered_date = formatted_response['delivered_date']

                    if 'shipping_date' in formatted_response:
                        order.shipping_date = formatted_response['shipping_date']

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

