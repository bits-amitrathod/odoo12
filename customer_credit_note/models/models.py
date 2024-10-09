
from odoo import models, fields, api,_
from odoo.exceptions import UserError,Warning


class CustomerCreditNote(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):

        account_journal = self.env['account.journal'].search([('id', '=', self.journal_id.id)])
        invoice_journal = self.env['account.journal'].search([('code', '=', 'INV')], limit=1)
        if account_journal.code == 'CRN':
            if self.env.context.get('journal_type') != 'sale':
                print('is CRN')
                res_partner = self.env['res.partner'].search([('id', '=',self.partner_id.id)])
                if res_partner.customer_rank > 0:
                    super(CustomerCreditNote, self).action_create_payments()
                    print('is CUSTOMER')
                    tax_string = []
                    line_string_all = []
                    account_obj = self.env['account.account'].search([('code', '=', '1310')])
                    account_receivable_obj = self.env['account.account'].search([('code', '=', '1200')])
                    for acc_move_line in self.line_ids:
                        name = 'Credit Transfer'
                        if acc_move_line.move_id.display_name:
                            name = name + ' PO# :' + acc_move_line.move_id.display_name

                        # credit move line entry

                        line_string_all.append((0, 0, {
                            'name': name,
                            'price_subtotal': acc_move_line.price_subtotal,
                            'price_unit': acc_move_line.price_unit,
                            'price_total': acc_move_line.price_total,
                            'balance': acc_move_line.balance,
                            'partner_id': acc_move_line.partner_id.id,
                            'account_id': account_receivable_obj.id,  # 7 is 	1200 Account Receivable
                            'quantity': acc_move_line.quantity,
                            'currency_id': acc_move_line.currency_id.id,
                            'credit': acc_move_line.credit,
                            'debit': acc_move_line.debit,
                            'amount_residual': acc_move_line.amount_residual,
                            'amount_residual_currency': acc_move_line.amount_residual_currency,
                            'display_type': 'payment_term',
                            'tax_base_amount':0
                        }))
                        # debit move line entry 1310
                        line_string_all.append((0, 0, {
                            'name': name,
                            'price_subtotal': abs(acc_move_line.balance),
                            'price_unit': abs(acc_move_line.balance),
                            'price_total': abs(acc_move_line.balance),
                            'partner_id': acc_move_line.partner_id.id,
                            'account_id': account_obj.id,
                            'quantity': 1,
                            'currency_id': acc_move_line.currency_id.id,
                            'debit': acc_move_line.credit,
                            'credit': acc_move_line.debit,
                            'amount_residual': abs(acc_move_line.amount_residual),
                            'amount_residual_currency': abs(acc_move_line.amount_residual_currency),
                            'display_type': 'product',
                            'tax_base_amount': 0
                        }))

                        acc_move = {
                            'id': False,
                            'invoice_date_due': fields.Date.today(),
                            'partner_id': self.partner_id.id,
                            'move_type': 'out_refund',
                            'state': 'draft',
                            'amount_untaxed': acc_move_line.move_id.amount_untaxed,
                            'amount_untaxed_signed': acc_move_line.move_id.amount_untaxed_signed,
                            'amount_tax': acc_move_line.move_id.amount_tax,
                            'amount_tax_signed': acc_move_line.move_id.amount_tax_signed,
                            'amount_total': acc_move_line.move_id.amount_total,
                            'amount_total_signed': acc_move_line.move_id.amount_total_signed,
                            'amount_residual_signed':acc_move_line.move_id.amount_residual_signed,
                            'amount_residual':acc_move_line.move_id.amount_residual,
                            'vendor_credit_flag': True,
                            'journal_id':invoice_journal.id, # 1 is INV
                            'extract_state':acc_move_line.move_id.extract_state,
                            'currency_id':acc_move_line.move_id.currency_id.id,
                            'date':acc_move_line.move_id.date
                            }
                        acc_move['line_ids'] = line_string_all
                    #     #'tax_line_ids': [(0, 0, tax_string)]
                        invoice_created = self.env['account.move'].create(acc_move)
                        invoice_created.action_post()

                else:
                    raise UserError('Payment Warning!\nCannot proceed with Payment Journal =" Credit Note " '
                                   'as the selected vendor is not a customer')
            else:
                raise UserError(
                    'Payment Warning!\n This Payment Journal option is available for Vendor Bill only')
        else:
            print('not CRN')
            super(CustomerCreditNote, self).action_create_payments()

    # TODO: UPD ODOO16 Note this Method is Not Used anywhere else in this module
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
    # user_id = fields.Many2one('res.users', string='Business Development', tracking=True,
    #                           readonly=True, states={'draft': [('readonly', False)]},
    #                           default=lambda self: self.env.user, copy=False)

    user_id = fields.Many2one('res.users', string='Business Development', tracking=True,
                              readonly=True, states={'draft': [('readonly', False)]},
                              copy=False)  # Remove the default here

    @api.model
    def create(self, vals):
        # setting user_id explicitly here by overriding create method if user id not found then set as current users id as default
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user.id
        return super(AccountInvoiceVendorCredit, self).create(vals)

