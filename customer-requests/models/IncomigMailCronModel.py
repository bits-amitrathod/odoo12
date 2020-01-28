# -*- coding: utf-8 -*-
import logging
import re
import poplib
import random
import string
import base64
import werkzeug.local
import werkzeug.wsgi

SUPERUSER_ID = 2

#----------------------------------------------------------
# RequestHandler
#----------------------------------------------------------
# Thread local global request object
_request_stack = werkzeug.local.LocalStack()
request = _request_stack()
from odoo import api, fields, models, tools, _
from datetime import datetime

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 1
MAIL_TIMEOUT = 60

poplib._MAXLINE = 65536

# Dumping data from Discuss(mail.message) to sps_customer_request(table)
class DumpDiscuss(models.Model):
    _inherit = 'mail.message'

    # Read/Unread Flag for incoming email from mail.channel
    # Only set is_read=True if file data is successfully dumped from 'mail.message' table to 'sps.customer.requests' table otherwise rollback
    is_read = fields.Boolean(Default=False)
    #To keep the count that how many times a particular document is processed
    processing_count = fields.Integer(Default= '0')

    @api.model
    def DumpData(self):
        # Fetching incoming_mail_server ids in orser to handle multiple incoming servers
        inc_mail_server_id =self.env['fetchmail.server'].search([])
        # Processing requests one by one as per incoming_mail_id_server
        for server_id in inc_mail_server_id:
            filtered_mail = server_id.user.split("@")[0]
            # Fetching channel name (record name) for particular email-id to receive email in that particular channel
            rec_mail_id_channel = self.env['mail.channel'].sudo().search([('alias_name', '=', filtered_mail)]).name
            # Fetching received email for particular created channel one at a time
            in_emails = self.env['mail.message'].sudo().search(
                [('model', '=', 'mail.channel'), ('is_read', '=', False), ('message_type', '=', 'email'),
                 ('record_name', '=', rec_mail_id_channel),
                 ('is_read', '!=', None)], limit=1, order='id asc')
            if in_emails:

                in_emails.write({'processing_count' : in_emails.processing_count+1})
                self.env.cr.commit()
                self.env.cr.savepoint()
                in_emails.write({'is_read': True})
                # No need for loop here as we are processing only one customer request at a time but in future CR might come to fetch multiple requests at a time hence used loop here
                if in_emails.processing_count and in_emails.processing_count <= 1 :
                    for message in in_emails:

                        try:
                            email_to = message.reply_to
                            match = re.search(r'[\w\.-]+@[\w\.-]+', email_to)
                            email_to = str(match.group(0))
                            _logger.info('Email to %r', email_to)
                            body = u''
                            email_from = message.email_from
                            email_subject = message.subject
                            subject = None
                            if email_subject:
                                subject = email_subject.replace(' ', '').lower()
                            else:
                                email_subject = ''
                            customer_email = ''
                            tmpl_type = None
                            saleforce_ac = None
                            attachments = None
                            file_extension = None
                            response = None
                            filename = None
                            res_partner = None
                            # Need to fetch attachment filename here to handle 'keep original mail' setting in Incoming_mail_cron -> advance tab'
                            # If setting is on there will be one extra attachment of original mail with the incoming mail otherwise customer attached attachments only
                            if message.attachment_ids:
                                filename = message.attachment_ids[0].name
                                if filename and filename != False:
                                    file_extension = filename[filename.rindex('.') + 1:]
                                    if file_extension == 'xls' or file_extension == 'xlsx' or file_extension == 'csv':
                                        attachments = message.attachment_ids[0].datas  # Reading the contents of customer attachment (Binary format) if there is any

                            if email_from is not None:
                                match = re.search(r'[\w\.-]+@[\w\.-]+', email_from)
                                email_from = str(match.group(0))
                                _logger.info('Email From : %r', email_from)

                            if subject and re.search('#(.*)#', subject):
                                match1 = re.search('#(.*)#', subject)
                                saleforce_ac = match1.group(1)
                                _logger.info('saleforce_ac: %r', str(saleforce_ac))
                                # find customer in res.partner
                                if saleforce_ac and saleforce_ac is not None:
                                    res_partner = self.env['res.partner'].search(
                                        [("saleforce_ac", "=ilike", saleforce_ac), ('prioritization', '=', True),
                                         ('on_hold', '=', False)])
                                    if len(res_partner) == 1:
                                        # when new email in inbox, send email to admin
                                        self.send_mail_with_attachment(str(email_from), str(email_subject),
                                                                       str(res_partner.name), attachments, in_emails)
                                        if res_partner.email:
                                            customer_email = res_partner.email
                                        else:
                                            _logger.info('Customer Email Id missing.')
                                            response = dict(errorCode=112, message='Customer Email Id missing.')
                                    elif len(res_partner) > 1:
                                        _logger.info('We have found Same Customer Id against multiple users. %r',
                                                     str(saleforce_ac))
                                        response = dict(errorCode=106,
                                                        message='We have found Same Customer Id against multiple customers.')
                                    else:
                                        res_partner = self.env['res.partner'].search([("saleforce_ac", "=ilike", saleforce_ac)])
                                        if res_partner and res_partner.email:
                                            customer_email = res_partner.email
                                        _logger.info(
                                            'Customer Id is not found in customers or prioritization setting is off  or Customer is on hold.: %r',
                                            str(saleforce_ac))
                                        response = dict(errorCode=107,
                                                        message='Customer Id is not found in customers  or prioritization setting is off or Customer is on hold.')
                                else:
                                    _logger.info('Customer Id is not found in email subject.')
                                    response = dict(errorCode=108, message='Customer Id is not found in email subject.')
                            else:
                                _logger.info("Customer Id not in email subject")
                                # File process against who has sent email.

                                # find customer in res.partner
                                if email_from and email_from is not None:
                                    res_partner = self.env['res.partner'].search(
                                        [("email", "=ilike", email_from), ('prioritization', '=', True),
                                         ('on_hold', '=', False)])
                                    if len(res_partner) == 1:
                                        # when new email in inbox, send email to admin
                                        self.send_mail_with_attachment(str(email_from), str(email_subject),
                                                                       str(res_partner.name), attachments, in_emails)
                                        if res_partner.email:
                                            customer_email = res_partner.email
                                        else:
                                            _logger.info('Customer Email Id missing.')
                                            response = dict(errorCode=112, message='Customer Email Id missing.')
                                        # pop_server.dele(num)
                                    elif len(res_partner) > 1:
                                        _logger.info('We have found same Customer Email against multiple customers. %r',
                                                     str(customer_email))
                                        response = dict(errorCode=109,
                                                        message='We have found same Customer Email against multiple customers.')
                                    else:
                                        res_partner = self.env['res.partner'].search([("email", "=ilike", email_from)])
                                        if res_partner and res_partner.email:
                                            customer_email = res_partner.email
                                        _logger.info(
                                            'Customer (Email) is not found in customers or prioritization setting is off or Customer is on hold: %r',
                                            str(email_from))
                                        response = dict(errorCode=110,
                                                        message='Customer (Email) is not found in customers or prioritization setting is off or Customer is on hold.')
                                else:
                                    _logger.info('Customer (Email) is not found in Customers.')
                                    response = dict(errorCode=111, message='Customer (Email) is not found in customers.')

                            if customer_email and res_partner.prioritization and res_partner.on_hold == False:
                                match = re.search(r'[\w\.-]+@[\w\.-]+', customer_email)
                                customer_email = str(match.group(0))
                                _logger.info('Customer Email Id %r', customer_email)

                                if attachments:
                                    if saleforce_ac is not None:
                                        users_model = self.env['res.partner'].search(
                                            [("saleforce_ac", "=ilike", saleforce_ac)])
                                        if users_model:
                                            if len(users_model) == 1:
                                                # filename = message.attachment_ids[0].name
                                                if filename:
                                                    try:
                                                        checksum = message.attachment_ids[0].checksum  # checksum neeed only to pass to function in order to get absolute path of file
                                                        file_path = message.attachment_ids[0]._get_path(attachments, checksum)[1]
                                                        _logger.info('File_path: %r', str(file_path))
                                                        response = self.env[
                                                            'sps.document.process'].process_document(users_model,
                                                                                                     file_path,
                                                                                                     tmpl_type,
                                                                                                     filename,
                                                                                                     email_from,
                                                                                                     'Email'
                                                                                                     )
                                                        self.env.cr.commit()  # Commit if attachment contents are properly written in sps_customer_requests table
                                                    except Exception as e:
                                                        _logger.info(str(e))
                                                        self.env.cr.rollback()  # Rollback if attachment contents are not properly written in sps_customer_requests table
                                            else:
                                                _logger.error(
                                                    'We have found same Customer Id against multiple Customer.')
                                                response = dict(errorCode=101,
                                                                message='We have found same Customer Id against multiple Customer.')
                                        else:
                                            _logger.info('Customer not found in customers.')
                                            response = dict(errorCode=102, message='Customer not found in customers.')
                                    else:
                                        users_model = self.env['res.partner'].search(
                                            [("email", "=ilike", customer_email)])
                                        if users_model:
                                            if len(users_model) == 1:
                                                # filename = message.attachment_ids[0].name
                                                if not filename is None:
                                                    try:
                                                        checksum = message.attachment_ids[0].checksum
                                                        file_path = message.attachment_ids[0]._get_path(attachments, checksum)[1]
                                                        _logger.info('File_path: %r', str(file_path))
                                                        response = self.env[
                                                            'sps.document.process'].process_document(users_model,
                                                                                                     file_path,
                                                                                                     tmpl_type,
                                                                                                     filename,
                                                                                                     email_from,
                                                                                                     'Email',
                                                                                                     )
                                                        self.env.cr.commit()
                                                    except Exception as e:
                                                        _logger.info(str(e))
                                                        self.env.cr.rollback()
                                            else:
                                                _logger.error(
                                                    'We have found same Customer Email against multiple Customer.')
                                                response = dict(errorCode=101,
                                                                message='We have found same Customer Email against multiple Customer.')
                                        else:
                                            _logger.info('Customer not found in customers.')
                                            response = dict(errorCode=102, message='Customer not found in customers.')
                                else:
                                    _logger.info("Customer has not attached requirement or inventory document.")
                                    response = dict(errorCode=104,
                                                    message='Customer has not attached requirement or inventory document.')

                            if "errorCode" in response:
                                self._error_code(response, attachments, customer_email, email_from, email_subject,
                                                 saleforce_ac, in_emails)

                        except Exception as ex:
                            self.env.cr.rollback()  # Rollback if attachment contents are not properly written in sps_customer_requests table
                            _logger.info('Error in First Try block %r',ex)

                else:
                    in_emails.write({'is_read': True})
                    response = dict(errorCode=105,
                                    message='File is too large to process!')
                    saleforce_ac = None
                    if in_emails.subject and re.search('#(.*)#', in_emails.subject):
                        re.search('#(.*)#', in_emails.subject)
                        match1 = re.search('#(.*)#', in_emails.subject)
                        saleforce_ac = match1.group(1)
                    else :
                        in_emails.subject = ''

                    if saleforce_ac and saleforce_ac is not None:
                        res_partner = self.env['res.partner'].search(
                            [("saleforce_ac", "=ilike", saleforce_ac), ('prioritization', '=', True),
                             ('on_hold', '=', False)])
                        if len(res_partner) == 1:
                            # when new email in inbox, send email to admin
                            if res_partner.email:
                                customer_email = res_partner.email
                            else:
                                customer_email = ''

                    self._error_code(response, in_emails.attachment_ids[0].datas, customer_email, in_emails.email_from, in_emails.subject,
                                      saleforce_ac, in_emails)

# This function is specific to update admin(via email) if there is any new customer request
    def send_mail_with_attachment(self, email_from, email_subject, customer_name, attachments,email_obj=None):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = self.env.ref('customer-requests.new_email_in_inbox').sudo()
        local_context = {'emailFrom': email_from, 'emailSubject': email_subject, 'date': today_date, 'customerName': customer_name}
        if attachments:
            for attachment in email_obj.attachment_ids[0]: # No need for loop here as we are processing only one attachment at a time but in future CR might come to process multiple attachments at a time hence used loop here
                try:
                    filename = email_obj.attachment_ids[0].name # we can also get filename in parameter list from the calling function
                    if filename is not None:
                        try:
                            file_contents_bytes = attachments
                            file_extension = filename[filename.rindex('.') + 1:]
                        except Exception as e:
                            _logger.info(str(e))
                    values = {'attachment_ids': [(0, 0, {'name': filename,
                                                        'type': 'binary',
                                                        'mimetype': 'application/' + file_extension,
                                                        'datas_fname': filename,
                                                        'datas': base64.b64encode(file_contents_bytes)})],
                             'model': None, 'res_id': False}
                    sent_email_template = template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
                    self.env['mail.mail'].sudo().browse(sent_email_template).write(values)
                except:
                    response = {'message': 'Unable to connect to SMTP Server'}
        else:
            try:
                template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
            except:
                response = {'message': 'Unable to connect to SMTP Server'}


    def _error_code(self, response, attachments, customer_email, email_from, email_subject, saleforce_ac=None, email_obj=None):
        response.update({'attachment': attachments})
        if saleforce_ac is not None or customer_email is not None:
            res_partners = self.env['res.partner'].search( ['|', ("saleforce_ac", "=ilike", saleforce_ac), ("email", "=ilike", customer_email)])
            if len(res_partners) > 1:
                customerName = ""
                for res_partner in res_partners:
                    if customerName == "":
                        customerName = res_partner['name']
                    else:
                        customerName = str(customerName) + "  ,  " + str(res_partner['name'])

            if len(res_partners) == 1:
                self.send_mail(str(email_from), str(email_subject), str(res_partners['name']), str(customer_email), response, email_obj)
            elif len(res_partners) > 1:
                self.send_mail(str(email_from), str(email_subject), customerName, str(customer_email), response, email_obj)
            else:
                self.send_mail(str(email_from), str(email_subject), '', str(customer_email) ,response, email_obj)
        else:
            self.send_mail(str(email_from), str(email_subject),'','',response,email_obj)

# This method is called from '_error_code' method to send mail to admin if there is any error in request processing
    def send_mail(self, email_from, email_subject, customer_name, customerEmail, response,email_obj=None):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = self.env.ref('customer-requests.set_log_email_response').sudo()
        local_context = {'emailFrom': email_from, 'emailSubject': email_subject, 'date': today_date, 'customerName': customer_name, 'email': customerEmail,  'reason' : response['message']}
        if response['attachment']:
            for attachment in email_obj.attachment_ids[0]:
                try:
                    filename = email_obj.attachment_ids[0].name # we can also get filename in parameter list from the calling function (Optimisation)
                    if filename is not None:
                        try:
                            file_contents_bytes = email_obj.attachment_ids[0].datas # we can also get file-contents in parameter list from the calling function (Optimisation)
                            file_extension = filename[filename.rindex('.') + 1:]
                            print('file extension in send_mail : ' + file_extension)
                        except Exception as e:
                            _logger.info(str(e))
                    values = {'attachment_ids': [(0, 0, {'name': filename,
                                                         'type': 'binary',
                                                         'mimetype': 'application/' + file_extension,
                                                         'datas_fname': filename,
                                                         'datas': base64.b64encode(file_contents_bytes)})],
                              'model': None, 'res_id': False}
                    sent_email_template = template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
                    self.env['mail.mail'].sudo().browse(sent_email_template).write(values)
                except:
                    response = {'message': 'Unable to connect to SMTP Server'}
        else:
            try:
                template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
            except:
                response = {'message': 'Unable to connect to SMTP Server'}


# This function is never used in this particular module
    @staticmethod
    def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


