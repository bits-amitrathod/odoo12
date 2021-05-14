from odoo import models, api, _, fields
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import datetime, timedelta


class ReportPartnerLedgerExtension(models.AbstractModel):
    _inherit = "account.partner.ledger"
    _description = "Partner Ledger"

    # @api.model
    # def _get_lines(self, options, line_id=None):
    #     offset = int(options.get('lines_offset', 0))
    #     lines = []
    #     context = self.env.context
    #     company_id = context.get('company_id') or self.env.user.company_id
    #     if line_id:
    #         line_id = int(line_id.split('_')[1]) or None
    #     elif options.get('partner_ids') and len(options.get('partner_ids')) == 1:
    #         # If a default partner is set, we only want to load the line referring to it.
    #         partner_id = options['partner_ids'][0]
    #         line_id = partner_id
    #     if line_id:
    #         if 'partner_' + str(line_id) not in options.get('unfolded_lines', []):
    #             options.get('unfolded_lines', []).append('partner_' + str(line_id))
    #
    #     grouped_partners = self._group_by_partner_id(options, line_id)
    #     sorted_partners = sorted(grouped_partners, key=lambda p: p.name or '')
    #     unfold_all = context.get('print_mode') and not options.get('unfolded_lines')
    #     total_initial_balance = total_debit = total_credit = total_balance = 0.0
    #     for partner in sorted_partners:
    #         debit = grouped_partners[partner]['debit']
    #         credit = grouped_partners[partner]['credit']
    #         balance = grouped_partners[partner]['balance']
    #         initial_balance = grouped_partners[partner]['initial_bal']['balance']
    #         total_initial_balance += initial_balance
    #         total_debit += debit
    #         total_credit += credit
    #         total_balance += balance
    #         columns = [self.format_value(initial_balance), self.format_value(debit), self.format_value(credit)]
    #         if self.user_has_groups('base.group_multi_currency'):
    #             columns.append('')
    #         columns.append(self.format_value(balance))
    #         # don't add header for `load more`
    #         if offset == 0:
    #             lines.append({
    #                 'id': 'partner_' + str(partner.id),
    #                 'name': partner.name,
    #                 'columns': [{'name': v} for v in columns],
    #                 'level': 2,
    #                 'trust': partner.trust,
    #                 'unfoldable': True,
    #                 'unfolded': 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all,
    #                 'colspan': 6,
    #             })
    #         user_company = self.env.user.company_id
    #         used_currency = user_company.currency_id
    #         if 'partner_' + str(partner.id) in options.get('unfolded_lines') or unfold_all:
    #             if offset == 0:
    #                 progress = initial_balance
    #             else:
    #                 progress = float(options.get('lines_progress', initial_balance))
    #             domain_lines = []
    #             amls = grouped_partners[partner]['lines']
    #
    #             remaining_lines = 0
    #             if not context.get('print_mode'):
    #                 remaining_lines = grouped_partners[partner]['total_lines'] - offset - len(amls)
    #
    #             for line in amls:
    #                 if options.get('cash_basis'):
    #                     line_debit = line.debit_cash_basis
    #                     line_credit = line.credit_cash_basis
    #                 else:
    #                     line_debit = line.debit
    #                     line_credit = line.credit
    #                 date = amls.env.context.get('date') or fields.Date.today()
    #                 line_currency = line.company_id.currency_id
    #                 line_debit = line_currency._convert(line_debit, used_currency, user_company, date)
    #                 line_credit = line_currency._convert(line_credit, used_currency, user_company, date)
    #                 progress_before = progress
    #                 progress = progress + line_debit - line_credit
    #                 caret_type = 'account.move'
    #                 if line.invoice_id:
    #                     caret_type = 'account.invoice.in' if line.invoice_id.type in (
    #                     'in_refund', 'in_invoice') else 'account.invoice.out'
    #                 elif line.payment_id:
    #                     caret_type = 'account.payment'
    #                 domain_columns = [line.journal_id.code, line.account_id.code, self._format_aml_name_char(line),
    #                                   line.date_maturity and format_date(self.env, line.date_maturity) or '',
    #                                   line.full_reconcile_id.name or '', self.format_value(progress_before),
    #                                   line_debit != 0 and self.format_value(line_debit) or '',
    #                                   line_credit != 0 and self.format_value(line_credit) or '']
    #                 if self.user_has_groups('base.group_multi_currency'):
    #                     domain_columns.append(self.with_context(no_format=False).format_value(line.amount_currency,
    #                                                                                           currency=line.currency_id) if line.amount_currency != 0 else '')
    #                 domain_columns.append(self.format_value(progress))
    #                 columns = [{'name': v} for v in domain_columns]
    #                 columns[3].update({'class': 'date'})
    #                 domain_lines.append({
    #                     'id': line.id,
    #                     'parent_id': 'partner_' + str(partner.id),
    #                     'name': format_date(self.env, line.date),
    #                     'class': 'date',
    #                     'columns': columns,
    #                     'caret_options': caret_type,
    #                     'level': 4,
    #                 })
    #
    #             # load more
    #             if remaining_lines > 0:
    #                 domain_lines.append({
    #                     'id': 'loadmore_%s' % partner.id,
    #                     'offset': offset + self.MAX_LINES,
    #                     'progress': progress,
    #                     'class': 'o_account_reports_load_more text-center',
    #                     'parent_id': 'partner_%s' % partner.id,
    #                     'name': _('Load more... (%s remaining)') % remaining_lines,
    #                     'colspan': 10 if self.user_has_groups('base.group_multi_currency') else 9,
    #                     'columns': [{}],
    #                 })
    #             lines += domain_lines
    #
    #     if not line_id:
    #         total_columns = ['', '', '', '', '', self.format_value(total_initial_balance),
    #                          self.format_value(total_debit), self.format_value(total_credit)]
    #         if self.user_has_groups('base.group_multi_currency'):
    #             total_columns.append('')
    #         total_columns.append(self.format_value(total_balance))
    #         lines.append({
    #             'id': 'grouped_partners_total',
    #             'name': _('Total'),
    #             'level': 0,
    #             'class': 'o_account_reports_domain_total',
    #             'columns': [{'name': v} for v in total_columns],
    #         })
    #     return lines

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
        columns = [
            {'name': aml['journal_code']},
            {'name': aml['account_code']},
            {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name'])},
            {'name': date_maturity or '', 'class': 'date'},
            {'name': aml['matching_number'] or ''},
            {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            if aml['currency_id']:
                currency = self.env['res.currency'].browse(aml['currency_id'])
                formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
                columns.append({'name': formatted_amount, 'class': 'number'})
            else:
                columns.append({'name': ''})
        columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
        return {
            'id': aml['id'],
            'parent_id': 'partner_%s' % (partner.id if partner else 0),
            'name': format_date(self.env, aml['date']),
            'class': 'text' + aml.get('class', ''),  # do not format as date to prevent text centering
            'columns': columns,
            'caret_options': caret_type,
            'level': 2,
        }

    def _format_aml_name_char(self, aml):
        name = '-'.join(
            (aml.move_id.name not in ['', '/'] and [aml.move_id.name] or []) +
            (aml.ref not in ['', '/', False] and [aml.ref] or []) +
            ([aml.name] if aml.name and aml.name not in ['', '/'] else [])
        )

        return name
