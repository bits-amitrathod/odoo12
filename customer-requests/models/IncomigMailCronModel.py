# -*- coding: utf-8 -*-

import email
import logging
import re
import poplib
import random
import string
import os
import html2text
import errno
from collections import namedtuple

import werkzeug.local
import werkzeug.wsgi
from odoo import SUPERUSER_ID

#----------------------------------------------------------
# RequestHandler
#----------------------------------------------------------
# Thread local global request object
_request_stack = werkzeug.local.LocalStack()

request = _request_stack()

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

from odoo import api, fields, models, tools, _

from datetime import datetime

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from email.message import Message

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

poplib._MAXLINE = 65536
#path = os.path.abspath(__file__)
#dir_path = os.path.dirname(os.path.dirname(os.path.dirname(path)))
#ATTACHMENT_DIR =  dir_path + "/Documents/attachments/"
ATTACHMENT_DIR = "/home/odoo/Documents/attachments/"


class IncomingMailCronModel(models.Model):
    _inherit = 'fetchmail.server'

    @api.multi
    def fetch_mail(self):
        for server in self:
            count, failed = 0, 0
            pop_server = None
            if server.type == 'pop':
                _logger.info('Server tpye is POP')
                try:
                    while True:
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        _logger.info('Server tpye is POP inside while')
                        _logger.info('total_size = %d', total_size)
                        _logger.info('num_messages = %d', num_messages)
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            _logger.info('Server tpye is POP inside while INSIDE FOR')
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            response = {'message':'File Uploaded Successfully'}

                            try:
                                if isinstance(message, xmlrpclib.Binary):
                                    message = bytes(message.data)
                                if isinstance(message, pycompat.text_type):
                                    message = message.encode('utf-8')
                                extract = getattr(email, 'message_from_bytes', email.message_from_string)
                                message = extract(message)
                                if not isinstance(message, Message):
                                    message = pycompat.to_native(message)
                                    message = email.message_from_string(message)
                                email_to = tools.decode_message_header(message, 'To')
                                match = re.search(r'[\w\.-]+@[\w\.-]+', email_to)
                                email_to = str(match.group(0))
                                _logger.info('Email to %r', email_to)
                                # if email_to == INCOMING_EMAIL_ID:
                                _Attachment = namedtuple('Attachment', ('fname', 'content', 'info'))
                                attachments = []
                                body = u''
                                subject = tools.decode_message_header(message, 'Subject').replace(' ','').lower()
                                email_from = None
                                tmpl_type = None

                                if '{customerid:' in subject:
                                    match1 = re.findall(r'{[\w\.-]+:[\w\.-]+', subject)
                                    saleforce_ac = match1[0].split(':')[1]
                                    # find customer in res.partner
                                    if saleforce_ac and saleforce_ac is not None:
                                        res_partner = self.env['res.partner'].search([("saleforce_ac", "=", saleforce_ac)])
                                        if len(res_partner) == 1:
                                            email_from = res_partner.email
                                        elif len(res_partner) > 1:
                                            _logger.info('We have found Same Customer Id against multiple users. %r', str(saleforce_ac))
                                            response = dict(errorCode=106, message='We have found Same Customer Id against multiple users.')
                                        else:
                                            _logger.info('Customer Id is not found in customer list : %r', str(saleforce_ac))
                                            response = dict(errorCode=107, message='Customer Id is not found in customer list.')
                                    else:
                                        _logger.info('Customer Id is not found in email subject.')
                                        response = dict(errorCode=108, message='Customer Id is not found in email subject.')
                                else:
                                    _logger.info('Customer Id is not found in email subject.')
                                    response = dict(errorCode=109, message='Customer Id is not found in email subject.')
                                    # email_from = tools.decode_message_header(message, 'From')

                                if email_from is not None:
                                    match = re.search(r'[\w\.-]+@[\w\.-]+', email_from)
                                    email_from = str(match.group(0))
                                    _logger.info('Email from %r', email_from)

                                    # if 'Inventory' in subject:
                                    #     tmpl_type = "Inventory"
                                    # elif 'Requirement' in subject:
                                    #     tmpl_type = "Requirement"

                                    if message.get_content_maintype() != 'text':
                                        alternative = False
                                        for part in message.walk():
                                            if part.get_content_type() == 'multipart/alternative':
                                                alternative = True
                                            if part.get_content_maintype() == 'multipart':
                                                continue  # skip container
                                            filename = part.get_param('filename', None, 'content-disposition')
                                            if not filename:
                                                filename = part.get_param('name', None)
                                            if filename:
                                                if isinstance(filename, tuple):
                                                    filename = email.utils.collapse_rfc2231_value(filename).strip()
                                                else:
                                                    filename = tools.decode_smtp_header(filename)
                                            encoding = part.get_content_charset()
                                            if filename and part.get('content-id'):
                                                inner_cid = part.get('content-id').strip('><')
                                                attachments.append(_Attachment(filename, part.get_payload(decode=True),
                                                                               {'cid': inner_cid}))
                                                continue
                                            if filename or part.get('content-disposition', '').strip().startswith(
                                                    'attachment'):
                                                attachments.append(
                                                    _Attachment(filename or 'attachment', part.get_payload(decode=True),
                                                                {}))
                                                continue
                                            if part.get_content_type() == 'text/plain' and (
                                                    not alternative or not body):
                                                body = tools.append_content_to_html(body, tools.ustr(
                                                    part.get_payload(decode=True), encoding, errors='replace'),
                                                                                    preserve=True)
                                            elif part.get_content_type() == 'text/html':
                                                body = tools.ustr(part.get_payload(decode=True), encoding,
                                                                  errors='replace')
                                            else:
                                                attachments.append(
                                                    _Attachment(filename or 'attachment', part.get_payload(decode=True),
                                                                {}))
                                        if len(attachments) > 0:
                                            encoding = message.get_content_charset()
                                            plain_text = html2text.HTML2Text()
                                            message_payload = plain_text.handle(
                                                tools.ustr(body, encoding, errors='replace'))

                                            #_logger.info('message payload: %r %r', message_payload, email_from)
                                            if email_from is not None:
                                                users_model = self.env['res.partner'].search([("email", "=ilike", email_from)])
                                                if users_model:
                                                    if len(users_model) == 1:
                                                        user_attachment_dir = ATTACHMENT_DIR + str(
                                                            datetime.now().strftime("%d%m%Y")) + "/" + str(
                                                            users_model.id) + "/"
                                                        if not os.path.exists(os.path.dirname(user_attachment_dir)):
                                                            try:
                                                                os.makedirs(os.path.dirname(user_attachment_dir))
                                                            except OSError as exc:
                                                                if exc.errno != errno.EEXIST:
                                                                    raise
                                                        for attachment in attachments:
                                                            filename = getattr(attachment, 'fname')
                                                            if not filename is None:
                                                                try:
                                                                    file_contents_bytes = getattr(attachment, 'content')
                                                                    file_path = user_attachment_dir + str(filename)
                                                                    file_ref = open(str(file_path), "wb+")
                                                                    file_ref.write(file_contents_bytes)
                                                                    file_ref.close()
                                                                    response = self.env['sps.document.process'].process_document(
                                                                        users_model, file_path, tmpl_type,filename, 'Email')
                                                                except Exception as e:
                                                                    _logger.info(str(e))
                                                    else:
                                                        _logger.error('We have found Same Email Id against multiple users %r', email_from)
                                                        response = dict(errorCode=101, message='We have found Same Email Id against multiple users.')
                                                else:
                                                    _logger.info('We have not found user in our contact list : %r', email_from)
                                                    response = dict(errorCode=102, message='User not found in our contact list.')
                                            else:
                                                _logger.info('We have not found user in our contact list : %r', email_from)
                                                response = dict(errorCode=103, message='User not found in our contact list.')
                                        else:
                                            _logger.info("User has not attached requirement or inventory documnet.")
                                            response = dict(errorCode=104, message='User has not attached requirement or inventory documnet.')
                                    else:
                                        _logger.info('This is not a multipart email')
                                        response = dict(errorCode=105, message='This is not a multipart email.')

                                pop_server.dele(num)

                                if "errorCode" in response:
                                    if email_from is not None:
                                        res_partners = self.env['res.partner'].search([("email", "=ilike", email_from)])
                                        if len(res_partners) > 1:
                                            customerName = ""
                                            for res_partner in res_partners:
                                                if customerName == "":
                                                    customerName = res_partner['name']
                                                else:
                                                    customerName = customerName + "  ,  " + res_partner['name']

                                        if len(res_partners) == 1:
                                            self.send_mail(str(res_partners['name']), str(email_from),str(response['message']))
                                        elif len(res_partners) > 1:
                                            self.send_mail(customerName, str(email_from),str(response['message']))
                                        else:
                                            self.send_mail('', str(email_from),str(response['message']))
                                    else:
                                        self.send_mail('', '', str(response['message']))

                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.type, server.name, exc_info=True)
                                failed += 1

                            if res_id and server.action_id:
                                server.action_id.with_context({
                                    'active_id': res_id,
                                    'active_ids': [res_id],
                                    'active_model': self.env.context.get("thread_model", server.object_id.model)
                                }).run()
                            self.env.cr.commit()
                        _logger.info('num_messages = %d',num_messages)
                        if num_messages < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num_messages,
                                     server.type, server.name, (num_messages - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type,
                                 server.name, exc_info=True)
                finally:
                    _logger.info('Server tpye is POP inside finally')
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})

        return super(IncomingMailCronModel, self).fetch_mail()

    @staticmethod
    def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def send_mail(self, customerName, email, reason):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = self.env.ref('customer-requests.set_log_email_response').sudo()
        local_context = {'customerName': customerName, 'email': email, 'date': today_date, 'reason': reason}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
        except:
            response = {'message': 'Unable to connect to SMTP Server'}
