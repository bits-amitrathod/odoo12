from odoo import models, api
import logging
from datetime import datetime
SUPERUSER_ID = 2

_logger = logging.getLogger(__name__)


class ProcessHighPriorityRequests(models.Model):
    _name = 'process.high.priority.requests'

    documents = set()

    @api.model
    def process_high_priority_requests(self, document_id=None, source=None):
        _logger.info('process high priority requests.')
        self.documents.clear()
        if source is None:
            document = self.env['sps.cust.uploaded.documents'].search([('status', '=', 'draft')], limit=1, order="id asc")
        elif source == 'Portal' and document_id and document_id is not None:
            document = self.env['sps.cust.uploaded.documents'].search([('id', '=', int(document_id)), ('status', '=', 'Portal In Process')])
        if len(document) == 1:
            if source == 'Portal':
                high_priority_requests = self.env['sps.customer.requests'].search(
                    [('document_id', '=', document.id), ('status', '=', 'New'), ('priority', '=', 0),
                     '|', ('required_quantity', '>', 0), ('quantity', '>', 0)])
            else:
                high_priority_requests = self.env['sps.customer.requests'].search(
                    [('document_id', '=', document.id), ('status', '=', 'New'), ('priority', '=', 0),
                     ('available_qty', '>', 0),
                     '|', ('required_quantity', '>', 0), ('quantity', '>', 0)])

            if len(high_priority_requests) > 0:
                try:
                    self.env.cr.savepoint()
                    high_priority_doc_pro_count = document.high_priority_doc_pro_count + 1
                    document.write({'high_priority_doc_pro_count': high_priority_doc_pro_count})
                    self.env.cr.commit()
                    if high_priority_doc_pro_count <= 2:
                        self.documents.add(document.id)
                        self.env['sps.customer.requests'].process_customer_requests(high_priority_requests, tuple(self.documents), source)
                        document.write({'document_processed_count': document.document_processed_count + 1})
                    else:
                        document.write({'status': 'On Hold'})
                        self.env.cr.commit()
                        self.send_on_hold_doc_mail(document.email_from, document.customer_id.name, document.customer_id.email, document.document_name, document.status, document.source, 'Unable to process file. May be file is too large.')
                except Exception as exc:
                    _logger.error("Error processing requests %r", exc)
            else:
                _logger.info('customer request count is 0.')
                document.write({'status': 'In Process', 'document_logs': 'Unfortunately, we are currently out of stock on the products that you requested. We have documented your request on your account.'})

            try:
                self.env['prioritization.engine.model'].check_uploaded_document_status(document.id)
            except Exception as exc:
                _logger.error("Error: updating document status %r", exc)

    def send_on_hold_doc_mail(self, email_from, customer_name, customer_email, document_name, document_status, source, reason):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = self.env.ref('prioritization_engine.on_hold_doc_response').sudo()
        local_context = {'emailFrom': email_from, 'customerName': customer_name, 'email': customer_email, 'documentName': document_name, 'documentStatus': document_status, 'source': source, 'date': today_date, 'reason': reason}
        try:
            template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
        except Exception as exc:
            _logger.error('Unable to connect to SMTP Server : %r', exc)
            response = {'message': 'Unable to connect to SMTP Server'}