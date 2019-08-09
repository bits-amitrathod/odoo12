from odoo.tools.misc import formatLang, format_date
from odoo import api, fields, models, _

INV_LINES_PER_STUB = 9
class report_print_check(models.Model):
    _inherit = 'account.payment'

    def get_pages(self):
        """ Returns the data structure used by the template : a list of dicts containing what to print on pages.
        """
        stub_pages = self.make_stub_pages() or [False]
        multi_stub = self.company_id.us_check_multi_stub
        pages = []
        parent_name=''
        if self.partner_id.parent_name:
            parent_name=self.partner_id.parent_name
        else:
            parent_name = self.partner_id.name
        for i, p in enumerate(stub_pages):
            pages.append({
                'sequence_number': self.check_number\
                    if (self.journal_id.check_manual_sequencing and self.check_number != 0)\
                    else False,
                'payment_date': format_date(self.env, self.payment_date),
                'partner_id': self.partner_id,
                'partner_name': self.partner_id.name,
                'parent': parent_name,
                'currency': self.currency_id,
                'state': self.state,
                'amount': formatLang(self.env, self.amount, currency_obj=self.currency_id) if i == 0 else 'VOID',
                'amount_in_word': self.fill_line(self.check_amount_in_words) if i == 0 else 'VOID',
                'memo': self.communication,
                'stub_cropped': not multi_stub and len(self.invoice_ids) > INV_LINES_PER_STUB,
                # If the payment does not reference an invoice, there is no stub line to display
                'stub_lines': p,
            })
        return pages