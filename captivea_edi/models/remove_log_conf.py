from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LogRemove(models.Model):
    _name = 'log.remove'
    _description = 'Remove Logs'

    document_type = fields.Selection([('850', '850 Customer PO'),
                                      ('855', '855 POACK'),
                                      ('810', '810 INVACK'),
                                      ('856', '856 SHIPACK')])
    remove_logs_days = fields.Integer('Remove Logs Older Than(In days)')
    is_active = fields.Boolean('Is Active?')

    @api.constrains('document_type')
    def validate_document_type(self):
        if self.search([('document_type', '=', self.document_type), ('id', '!=', self.id)]):
            raise ValidationError(
                _("Duplicate Log removal rule. You can't create another rule for same document type."))

    def get_processed_logs(self, logs):
        processed_logs = self.env['setu.edi.log']
        pickings_ack = invoices_ack = False
        for log_id in logs:
            sales = log_id.picking_ids.mapped('sale_id') if log_id.document_type == '856' else log_id.sale_id

            pickings = sales and sales.picking_ids.filtered(lambda pick: pick.state != 'cancel') or False
            invoices = sales and sales.invoice_ids.filtered(lambda inv: inv.state != 'cancel') or False
            sales_ack = sales.mapped('poack_created')
            pickings_ack = pickings.mapped('asn_created') if pickings else pickings_ack
            invoices_ack = invoices.mapped('invn_sent') if invoices else invoices_ack
            if pickings and invoices and False not in sales_ack + pickings_ack + invoices_ack:
                processed_logs |= log_id
        return processed_logs

    def run_log_removal_cron(self):
        """
            This function is used to remove the EDI logs that are older than the specified number of days.
            The rules for removing the logs are defined in the Log Removal Rules.
            The rules are applied in the following order:
            1. 850 Customer PO
            2. 855 POACK
            3. 810 INVACK
            4. 856 SHIPACK
            If a log is processed by multiple rules, it is only removed once.
            The function gets the processed logs and removes them.
        """
        logs_to_remove = self.env['setu.edi.log']
        rule_850 = self.search([('document_type', '=', '850'), ('is_active', '=', True)])
        rule_855 = self.search([('document_type', '=', '855'), ('is_active', '=', True)])
        rule_856 = self.search([('document_type', '=', '856'), ('is_active', '=', True)])
        rule_810 = self.search([('document_type', '=', '810'), ('is_active', '=', True)])

        if rule_850 and rule_850.remove_logs_days != 0:
            logs = self.env['setu.edi.log'].search(
                [('document_type', '=', '850'),
                 ('create_date', '<=', date.today() - relativedelta(days=rule_850.remove_logs_days))])
            logs_to_remove |= logs.filtered(lambda log: log.status == 'fail')
            logs = logs.filtered(lambda log: log.status != 'fail')
            processed_logs = self.get_processed_logs(logs)
            logs_to_remove |= processed_logs

        if rule_855 and rule_855.remove_logs_days != 0:
            logs = self.env['setu.edi.log'].search(
                [('document_type', '=', '855'),
                 ('create_date', '<=', date.today() - relativedelta(days=rule_855.remove_logs_days))])
            logs_to_remove |= logs.filtered(lambda log: log.status == 'fail')
            logs = logs.filtered(lambda log: log.status != 'fail')
            processed_logs = self.get_processed_logs(logs)
            logs_to_remove |= processed_logs

        if rule_856 and rule_856.remove_logs_days != 0:
            logs = self.env['setu.edi.log'].search(
                [('document_type', '=', '856'),
                 ('create_date', '<=', date.today() - relativedelta(days=rule_856.remove_logs_days))])
            logs = logs.filtered(lambda log: log.document_type == '856')
            logs_to_remove |= logs.filtered(lambda log: log.status == 'fail')
            logs = logs.filtered(lambda log: log.status != 'fail')
            processed_logs = self.get_processed_logs(logs)
            logs_to_remove |= processed_logs

        if rule_810 and rule_810.remove_logs_days != 0:
            logs = self.env['setu.edi.log'].search(
                [('document_type', '=', '810'),
                 ('create_date', '<=', date.today() - relativedelta(days=rule_810.remove_logs_days))])
            logs = logs.filtered(lambda log: log.document_type == '810')
            logs_to_remove |= logs.filtered(lambda log: log.status == 'fail')
            logs = logs.filtered(lambda log: log.status != 'fail')
            processed_logs = self.get_processed_logs(logs)
            logs_to_remove |= processed_logs

        logs_to_remove.unlink()
