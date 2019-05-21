# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError,Warning


class CustomerCreditNote(models.Model):
    _inherit = "account.payment"

    # def init(self):
    #     current_lib_account = self.env['account.account'].search([('code', '=', '111000')])
    #     account_obj_fetch = self.env['account.account'].search([('code', '=', '121212')])
    #     if account_obj_fetch.id is False:
    #         new_account_obj = {
    #             'id': False,
    #             'name': 'Credit Transfer Test',
    #             'code': '1212129', 'user_type_id': current_lib_account.id
    #         }
    #         account_chart_obj = self.env['account.account'].create(new_account_obj)
    #
    #
    #     account_journal = self.env['account.journal'].search([('code', '=', 'CRN')])
    #     if account_journal.id is False:
    #         journal_obj = {
    #             'id': False,
    #             'name': 'Credit Note',
    #             'code': 'CRN', 'type': 'cash', 'default_credit_account_id': account_obj_fetch.id,
    #             'default_debit_account_id': account_obj_fetch.id
    #         }
    #         account_journal_obj = self.env['account.journal'].create(journal_obj)

    def action_validate_invoice_payment(self):

        account_journal = self.env['account.journal'].search([('id', '=', self.journal_id.id)])
        if account_journal.code == 'CRN':
            if self.env.context.get('journal_type') != 'sale':
                print('is CRN')
                res_partner = self.env['res.partner'].search([('id', '=',self.partner_id.id)])
                if res_partner.customer is True:
                    super(CustomerCreditNote, self).action_validate_invoice_payment()
                    print('is CUSTOMER')
                    invoice_ids = self.invoice_ids.ids
                    for invoice_id in invoice_ids:
                        invoice_obj_fetch = self.env['account.invoice'].browse(invoice_id)
                        tax_string = []
                        line_string_all = []
                        invoice_line_obj_list = self.env['account.invoice.line'].search(
                            [('invoice_id', 'in', invoice_obj_fetch.ids)])

                        account_obj = self.env['account.account'].search([('code', '=', '121212')])
                        for line in invoice_line_obj_list:
                            line_string_all.append((0, 0, {
                                'name': 'Credit Transfer', 'price_subtotal': line.price_subtotal,
                                'price_unit': line.price_unit,
                                'price_total': line.price_total, 'price_subtotal_signed': line.price_subtotal_signed
                                , 'account_id': account_obj.id, 'quantity': line.quantity,
                                'currency_id': line.currency_id.id,
                                'uom_id': line.uom_id.id
                            }))

                        # account_tax_lines = self.env['account.invoice.tax'].search(
                        #     [('invoice_id', 'in', invoice_obj_fetch.ids)])
                        # for tax in account_tax_lines:
                        #     tax_string.append((0, 0, {
                        #         'account_id': tax.account_id.id, 'amount': tax.amount,
                        #         'amount_rounding': tax.amount_rounding,
                        #         'amount_total': tax.amount_total, 'currency_id': tax.currency_id.id,
                        #         'tax_id': tax.tax_id.id,
                        #         'name': tax.name
                        #     }))

                        invoice_obj = {
                            'id': False,
                            'date_due': fields.Date.today(),
                            'partner_id': self.partner_id.id, 'reference_type': 'none', 'type': 'out_refund', 'state': 'draft',
                            'amount_untaxed': invoice_obj_fetch.amount_untaxed,
                            'amount_untaxed_signed': invoice_obj_fetch.amount_untaxed_signed,
                            'amount_tax': invoice_obj_fetch.amount_tax,
                            'amount_total': invoice_obj_fetch.amount_total,
                            'amount_total_signed': invoice_obj_fetch.amount_total_signed,
                            'amount_total_company_signed': invoice_obj_fetch.amount_total_company_signed,
                            'residual': invoice_obj_fetch.residual, 'residual_signed': invoice_obj_fetch.residual_signed,
                            'residual_company_signed': invoice_obj_fetch.residual_company_signed,
                            'reconciled': False,
                            'sent': 'false', 'vendor_credit_flag': True
                        }
                        invoice_obj['invoice_line_ids'] = line_string_all
                        #'tax_line_ids': [(0, 0, tax_string)]
                        invoice_created = self.env['account.invoice'].create(invoice_obj)
                        invoice_created.action_invoice_open()
                else:
                    raise Warning(_(
                        'Payment Warning!\nCannot proceed with Payment Journal =" Credit Note " '
                        'as the selected vendor is not a customer'))
            else:
                raise Warning(_(
                    'Payment Warning!\n This Payment Journal option is available for Vendor Bill only'))
        else:
            print('not CRN')
            super(CustomerCreditNote, self).action_validate_invoice_payment()


class AccountInvoiceVendorCredit(models.Model):
    _inherit = "account.invoice"
    vendor_credit_flag = fields.Boolean('Credit Note Flag', default=False)
