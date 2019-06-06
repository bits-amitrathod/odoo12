# -*- coding: utf-8 -*-
import os

import suds
from fedex_request import FedexRequest, LogPlugin
from odoo import models
from odoo.exceptions import UserError
from odoo.http import request
from suds.client import Client


class FedexApiCstm(FedexRequest):

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

    def set_version(self, serviceId, major, intermediate, minor):
        self.Version = self.client.factory.create('VersionId')
        self.Version.ServiceId = serviceId
        self.Version.Major = major
        self.Version.Intermediate = intermediate
        self.Version.Minor = minor

    def set_tracking_umber(self, trackingNumber):
        self.selectionDetails = self.client.factory.create('TrackSelectionDetail')
        self.selectionDetails.PackageIdentifier = self.client.factory.create('TrackPackageIdentifier')
        self.selectionDetails.PackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
        self.selectionDetails.PackageIdentifier.Value = trackingNumber
        delattr(self.selectionDetails, 'OperatingCompany')
        delattr(self.selectionDetails, 'CarrierCode')

    def process_track_request(self):

        formatted_response = {}

        try:
            self.response = self.client.service.track(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                      ClientDetail=self.ClientDetail,
                                                      Version=self.Version,
                                                      SelectionDetails=self.selectionDetails)

            if self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE' and \
                    self.response.CompletedTrackDetails[0].TrackDetails[0].Notification.Severity != 'ERROR':
                if 'Events' in self.response.CompletedTrackDetails[0].TrackDetails[0]:
                    event = self.response.CompletedTrackDetails[0].TrackDetails[0].Events[0]
                    formatted_response['data'] = "<b>Tracking Number:</b>" + \
                                                 self.response.CompletedTrackDetails[0].TrackDetails[0].TrackingNumber + \
                                                 "<br/><b>Status</b>: " + event.EventDescription + \
                                                 "<br/><b>Date: </b>" + event.Timestamp.strftime("%m/%d/%Y %I:%M:%S %p")
                    address = "<br/> <b>Address:</b> <br>"
                    if event.Address:
                        address += event.Address.Residential + "<br/>" if 'Residential' in event.Address and event.Address.Residential else ""
                        address += event.Address.City + "<br/>" if 'City' in event.Address and event.Address.City else ""
                        address += event.Address.StateOrProvinceCode + "<br/>" if 'StateOrProvinceCode' in event.Address and event.Address.StateOrProvinceCode else ""
                        address += event.Address.CountryName + "<br/>" if 'CountryName' in event.Address and event.Address.CountryName else ""
                        address += event.Address.PostalCode + "<br/>" if 'PostalCode' in event.Address and event.Address.PostalCode else ""
                        formatted_response['data'] += address
                else:
                    formatted_response['data'] = "No Data"


            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if
                                            (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                if errors_message == '':
                    errors_message = "Please try again later."
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join(
                    [("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"

        return formatted_response


class FedexDelivery(models.Model):
    _inherit = 'delivery.carrier'

    def fedex_track_request(self, order, tracking_numbers):
        # self.prod_environment
        for tracking_number in tracking_numbers:
            srm = FedexApiCstm(self.log_xml, prod_environment=True)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            # srm.web_authentication_detail('hFceAv3XJUumwZaS', 'jQDWagVknWD3OZIe3jn9vdtab')
            # srm.client_detail(339923531, 114470940)

            srm.set_version('trck', 16, 0, 0)
            srm.set_tracking_umber(tracking_number)
            logmessage = srm.process_track_request()
            if 'data' in logmessage:
                order.message_post(body=logmessage['data'])
            else:
                raise UserError(logmessage['errors_message'])
