
from odoo import models, fields, api,_
from odoo.exceptions import UserError,Warning


class CustomerCreditNote(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):

        account_journal = self.env['account.journal'].search([('id', '=', self.journal_id.id)])
        if account_journal.code == 'CRN':
            if self.env.context.get('journal_type') != 'sale':
                print('is CRN')
                res_partner = self.env['res.partner'].search([('id', '=',self.partner_id.id)])
                if res_partner.customer_rank > 0:
                    super(CustomerCreditNote, self).action_create_payments()
                    print('is CUSTOMER')
                    self.line_ids
                    # acc_move_ids = self.invoice_ids.ids
                    # for acc_move_id in invoice_ids:
                    #     invoice_obj_fetch = self.env['account.move'].browse(acc_move_id)
                    tax_string = []
                    line_string_all = []
                    #     invoice_line_obj_list = self.env['account.invoice.line'].search( [('invoice_id', 'in', invoice_obj_fetch.ids)])

                    account_obj = self.env['account.account'].search([('code', '=', '1310')])
                    for acc_move_line in self.line_ids:
                        name = 'Credit Transfer'
                        self.line_ids[0].move_id.display_name
                        if acc_move_line.move_id.display_name:
                            name = name + ' PO# :' + acc_move_line.move_id.display_name
                       # if acc_move_line.move_id.number:
                       #    name = name + ' Bill# :' + invoice_obj_fetch.number

                        line_string_all.append((0, 0, {
                            'name': name,
                            'price_subtotal': acc_move_line.price_subtotal,
                            'price_unit': acc_move_line.price_unit,
                            'price_total': acc_move_line.price_total,
                            # 'price_subtotal_signed': acc_move_line.price_subtotal_signed,
                            'account_id': account_obj.id,
                            'quantity': acc_move_line.quantity,
                            'currency_id': acc_move_line.currency_id.id,
                            # 'uom_id': acc_move_line.uom_id.id
                        }))

                        acc_move = {
                            'id': False,
                            # 'date_due': fields.Date.today(),
                            # 'partner_id': self.partner_id.id,
                            # 'reference_type': 'none',
                            # 'type': 'out_refund',
                            # 'state': 'draft',
                            # 'amount_untaxed': acc_move_line.move_id.amount_untaxed,
                            # 'amount_untaxed_signed': acc_move_line.move_id.amount_untaxed_signed,
                            # 'amount_tax': acc_move_line.move_id.amount_tax,
                            # 'amount_total': acc_move_line.move_id.amount_total,
                            # 'amount_total_signed': acc_move_line.move_id.amount_total_signed,
                            # 'amount_total_company_signed': acc_move_line.move_id.amount_total_company_signed,
                            # 'residual': acc_move_line.move_id.residual,
                            # 'residual_signed': acc_move_line.move_id.residual_signed,
                            # 'residual_company_signed': acc_move_line.move_id.residual_company_signed,
                            # 'reconciled': False,
                            # 'sent': 'false',
                            # 'vendor_credit_flag': True
                            }
                        acc_move['line_ids'] = line_string_all
                    #     #'tax_line_ids': [(0, 0, tax_string)]
                        invoice_created = self.env['account.move'].create(acc_move)
                        # invoice_created.action_invoice_open()
                else:
                    raise Warning(_(
                        'Payment Warning!\nCannot proceed with Payment Journal =" Credit Note " '
                        'as the selected vendor is not a customer'))
            else:
                raise Warning(_(
                    'Payment Warning!\n This Payment Journal option is available for Vendor Bill only'))
        else:
            print('not CRN')
            super(CustomerCreditNote, self).action_create_payments()

    def _get_counterpart_move_line_vals(self, invoice=False):
        if self.payment_type == 'transfer':
            name = self.name
        else:
            name = ''
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment Received")
                elif self.payment_type == 'outbound':
                    name += _("Customer Credit Note")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Credit Note")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment Received")
            if invoice:
                name += ': '
                for inv in invoice:
                    if inv.move_id:
                        name += inv.number + ', '
                name = name[:len(name)-2]
        return {
            'name': name,
            'account_id': self.destination_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
        }


class AccountInvoiceVendorCredit(models.Model):
    _inherit = "account.move"
    vendor_credit_flag = fields.Boolean('Credit Note Flag', default=False)
    user_id = fields.Many2one('res.users', string='Business Development', track_visibility='onchange',
                              readonly=True, states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.user, copy=False)