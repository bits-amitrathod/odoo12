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

# Read/Unread Flag for incoming email
    is_read = fields.Boolean(Default=False)

    @api.model
    def DumpData(self):
        in_emails = self.env['mail.message'].sudo().search(
            [('model', '=', 'mail.channel'), ('is_read', '=', False), ('record_name', '=', 'general'),
             ('is_read', '!=', None)], limit=1, order='id asc')
        in_emails.write({'is_read': True})

        for message in in_emails:

            try:
                email_to = message.reply_to
                match = re.search(r'[\w\.-]+@[\w\.-]+', email_to)
                email_to = str(match.group(0))
                _logger.info('Email to %r', email_to)
                body = u''
                email_from = message.email_from
                email_subject = message.subject
                subject = email_subject.replace(' ', '').lower()
                customer_email = None
                tmpl_type = None
                saleforce_ac = None
                attachments = None
                file_extension = None

                filename = message.attachment_ids.name
                if filename and filename != False:
                        file_extension = filename[filename.rindex('.') + 1:]

                if file_extension == 'xls' or file_extension == 'xlsx' or file_extension == 'csv':
                        attachments = message.attachment_ids[0].datas

                if email_from is not None:
                    match = re.search(r'[\w\.-]+@[\w\.-]+', email_from)
                    email_from = str(match.group(0))
                    _logger.info('Email From : %r', email_from)

                if re.search('#(.*)#', subject):
                    match1 = re.search('#(.*)#', subject)
                    saleforce_ac = match1.group(1)
                    _logger.info('saleforce_ac: %r', str(saleforce_ac))
                    # find customer in res.partner
                    if saleforce_ac and saleforce_ac is not None:
                        res_partner = self.env['res.partner'].search(
                            [("saleforce_ac", "=ilike", saleforce_ac), ('prioritization', '=', True)])
                        if len(res_partner) == 1:
                            # when new email in inbox, send email to admin
                            self.send_mail_with_attachment(str(email_from), str(email_subject),
                                                           str(res_partner.name), attachments,in_emails)
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
                            _logger.info(
                                'Customer Id is not found in customers or prioritization setting is off.: %r',
                                str(saleforce_ac))
                            response = dict(errorCode=107,
                                            message='Customer Id is not found in customers  or prioritization setting is off.')
                    else:
                        _logger.info('Customer Id is not found in email subject.')
                        response = dict(errorCode=108, message='Customer Id is not found in email subject.')
                else:
                    _logger.info("Customer Id not in email subject")
                    # File process against who has sent email.

                    # find customer in res.partner
                    if email_from and email_from is not None:
                        res_partner = self.env['res.partner'].search([("email", "=ilike", email_from)])
                        if len(res_partner) == 1:
                            # when new email in inbox, send email to admin
                            self.send_mail_with_attachment(str(email_from), str(email_subject),
                                                           str(res_partner.name), attachments,in_emails)
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
                            _logger.info('Customer (Email) is not found in customers : %r', str(email_from))
                            response = dict(errorCode=110,
                                            message='Customer (Email) is not found in customers.')
                    else:
                        _logger.info('Customer (Email) is not found in Customers.')
                        response = dict(errorCode=111,
                                        message='Customer (Email) is not found in customers.')

                if customer_email is not None:
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
                                            self.env.cr.savepoint()
                                            checksum = message.attachment_ids[0].checksum
                                            file_path = message.attachment_ids[0]._get_path(attachments, checksum)[1]
                                            response = self.env[
                                                'sps.document.process'].process_document(users_model,
                                                                                         file_path,
                                                                                         tmpl_type,
                                                                                         filename,
                                                                                         email_from,
                                                                                         'Email'
                                                                                         )
                                            self.env.cr.commit()

                                        except Exception as e:
                                            _logger.info(str(e))
                                            self.env.cr.rollback()

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
                                    # when new email in inbox, send email to admin
                                    self.send_mail_with_attachment(str(email_from), str(email_subject), str(res_partner.name), attachments,in_emails)

                                    if not filename is None:
                                        try:
                                            self.env.cr.savepoint()
                                            checksum = message.attachment_ids[0].checksum
                                            file_path = message.attachment_ids[0]._get_path(attachments, checksum)[1]
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
                    self._error_code(response, saleforce_ac, attachments, customer_email, email_from, email_subject,in_emails)

            except Exception as ex:
                print(ex)


    def send_mail_with_attachment(self, email_from, email_subject, customer_name, attachments,email_obj):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = self.env.ref('customer-requests.new_email_in_inbox').sudo()
        local_context = {'emailFrom': email_from, 'emailSubject': email_subject, 'date': today_date, 'customerName': customer_name}
        if attachments:
            for attachment in email_obj.attachment_ids[0]:
                try:
                    filename = email_obj.attachment_ids[0].name
                    if filename is not None:
                        try:
                            file_contents_bytes = attachments
                            file_extension = filename[filename.rindex('.') + 1:]
                            print('file extension in send_mail_with_attachment : '+file_extension)
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


    def _error_code(self, response, saleforce_ac, attachments, customer_email, email_from, email_subject,email_obj):
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
                self.send_mail(str(email_from), str(email_subject), str(res_partners['name']), response['attachment'],email_obj)
            elif len(res_partners) > 1:
                self.send_mail(str(email_from), str(email_subject), customerName, response['attachment'],email_obj)
            else:
                self.send_mail(str(email_from), str(email_subject), '', response['attachment'],email_obj)
        else:
            self.send_mail(str(email_from), str(email_subject),response['attachment'],email_obj)


    def send_mail(self, email_from, email_subject, customer_name, attachments,email_obj):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = self.env.ref('customer-requests.new_email_in_inbox').sudo()
        local_context = {'emailFrom': email_from, 'emailSubject': email_subject, 'date': today_date, 'customerName': customer_name}
        if attachments:
            for attachment in email_obj.attachment_ids[0]:
                try:
                    filename = email_obj.attachment_ids[0].name
                    if filename is not None:
                        try:
                            file_contents_bytes = email_obj.attachment_ids[0].datas
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

    @staticmethod
    def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


