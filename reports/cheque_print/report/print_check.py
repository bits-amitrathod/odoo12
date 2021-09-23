from odoo.tools.misc import formatLang, format_date
from odoo import api, fields, models, _

INV_LINES_PER_STUB = 9
class report_print_check(models.Model):
    _inherit = 'account.payment'

    def set_check_amount_in_words(self):
        for payment in self:
            payment.check_amount_in_words = payment.currency_id.amount_to_text(payment.amount) if payment.currency_id else ''

    def _check_build_page_info(self, i, p):
        multi_stub = self.company_id.account_check_printing_multi_stub
        # self.set_check_amount_in_words()
        parent_name = ''
        if self.partner_id.parent_id:
            partner_id = self.partner_id
            while partner_id.parent_id:
                partner_id = partner_id.parent_id
            parent_name = partner_id.name
        else:
            parent_name = self.partner_id.name

        # return {
        #     'sequence_number': self.check_number if (self.journal_id.check_manual_sequencing and self.check_number != 0) else False,
        #     'payment_date': format_date(self.env, self.payment_date),
        #     'partner_id': self.partner_id,
        #     'partner_name': self.partner_id.name,
        #     'currency': self.currency_id,
        #     'state': self.state,
        #     'amount': formatLang(self.env, self.amount, currency_obj=self.currency_id) if i == 0 else 'VOID',
        #     'amount_in_word': self._check_fill_line(self.check_amount_in_words) if i == 0 else 'VOID',
        #     'memo': self.communication,
        #     'stub_cropped': not multi_stub and len(self.invoice_ids) > INV_LINES_PER_STUB,
        #     # If the payment does not reference an invoice, there is no stub line to display
        #     'stub_lines': p,
        #     'parent': parent_name,
        # }

        return {
            'sequence_number': self.check_number,
            'manual_sequencing': self.journal_id.check_manual_sequencing,
            'payment_date': format_date(self.env, self.date),
            'date': format_date(self.env, self.date),
            'partner_id': self.partner_id,
            'partner_name': self.partner_id.name,
            'currency': self.currency_id,
            'state': self.state,
            'amount': formatLang(self.env, self.amount, currency_obj=self.currency_id) if i == 0 else 'VOID',
            'amount_in_word': self._check_fill_line(self.check_amount_in_words) if i == 0 else 'VOID',
            'memo': self.ref,
            'stub_cropped': not multi_stub and len(self.move_id._get_reconciled_invoices()) > INV_LINES_PER_STUB,
            # If the payment does not reference an invoice, there is no stub line to display
            'stub_lines': p,
            'parent': parent_name,
        }