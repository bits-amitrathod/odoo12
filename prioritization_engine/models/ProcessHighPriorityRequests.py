from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class ProcessHighPriorityRequests(models.Model):
    _name = 'process.high.priority.requests'

    @api.model
    @api.multi
    def process_high_priority_requests(self):
        _logger.info('process high priority requests.')

        document = self.env['sps.cust.uploaded.documents'].search([('status', '=', 'draft')], limit=1, order="id asc")

        high_priority_requests = self.env['sps.customer.requests'].search([('document_id', '=', document.id), ('status', '=', 'New'), ('priority', '=', 0), ('available_qty', '>', 0)])

        if len(high_priority_requests) > 0:
            try:
                self.env['sps.customer.requests'].process_customer_requests(high_priority_requests)
            except Exception as exc:
                _logger.error("Error processing requests %r", exc)
        else:
            _logger.info('customer request count is 0.')

        try:
            self.env['prioritization.engine.model'].check_uploaded_document_status(document.id)
        except Exception as exc:
            _logger.error("Error: updating document status %r", exc)
