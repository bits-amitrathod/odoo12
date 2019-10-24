
from odoo import models, fields, api, _,tools
import base64
import threading
from odoo.modules import get_module_resource
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

class VendorBillPartnerName(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice address'),
         ('delivery', 'Shipping address'),
         ('other', 'AP Address'),
         # ('private', 'Private Address'),
         # ('ap', 'AP Address'),
         ], string='Address Type',
        default='contact',
        help="Used to select automatically the right address according to the context in sales and purchases documents.")

    @api.multi
    def name_get(self):

        res = []
        for partner in self:
            name = partner.name or ''
            if (self.env.context.get('vendor_bill_partner_name_display_name') and True != ('show_address' in self._context)) or\
                    (self.env.context.get('vendor_payment_partner_name_display_name') and True != ('show_address' in self._context)) :

            # or\
            #     (self.env.context.get('sale_invoice_sipping_partner_name_display_name') and True != ('show_address_only' in self._context ))   or\
            #         (self.env.context.get('sale_invoice_partner_name_display_name') and True != ('show_address_only' in self._context ) ) \

                if partner.company_name or partner.parent_id:
                    if not name and partner.type in ['invoice', 'delivery', 'other','ap']:
                        name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                    if not partner.is_company:
                        if partner.type :
                            if partner.type == 'other':
                                typ = 'AP'
                                name = "%s :- %s ,%s" % (typ,
                                                         partner.commercial_company_name or partner.parent_id.name,
                                                         name)
                            else:
                                name = "%s :- %s ,%s" % ((partner.type).upper(),
                                                         partner.commercial_company_name or partner.parent_id.name,
                                                         name)
                else:
                    if partner.type:
                        name = "%s :- %s" % (('main').upper(),
                                              partner.commercial_company_name or partner.name)
            else:
                if partner.company_name or partner.parent_id:
                    if not name and partner.type in ['invoice', 'delivery', 'other','ap']:
                        name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                    if not partner.is_company:
                        name = "%s ,%s" % (partner.commercial_company_name or partner.parent_id.name,name)

            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

    @api.model
    def _get_default_image(self, partner_type, is_company, parent_id):
        super_return = super(VendorBillPartnerName, self)._get_default_image(partner_type, is_company, parent_id)
        colorize, img_path, image = False, False, False

        if super_return and partner_type == 'other':
            if not image:
                img_path = get_module_resource('vendor_bill_partner_name', 'static/src/img', 'cart.png')
                colorize = True

            if img_path:
                with open(img_path, 'rb') as f:
                    image = f.read()
        # if image and colorize:
        #     image = tools.image_colorize(image)

        return tools.image_resize_image_big(base64.b64encode(image)) if image and colorize else super_return


    @api.model
    def _get_default_image(self, partner_type, is_company, parent_id):
        super_return=super(VendorBillPartnerName, self). _get_default_image(partner_type, is_company, parent_id)
        colorize, img_path, image = False, False, False

        if super_return and partner_type == 'other':
            if not image :
                img_path = get_module_resource('vendor_bill_partner_name', 'static/src/img', 'cart.png')
                colorize = True

            if img_path:
                with open(img_path, 'rb') as f:
                    image = f.read()
        # if image and colorize:
        #     image = tools.image_colorize(image)

        return tools.image_resize_image_big(base64.b64encode(image)) if image and colorize else super_return

class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def create(self, values):
        # Override the original create function for the res.partner model
        record = super(account_invoice, self).create(values)

        # Change the values of a variable in this super function
        # record['passed_override_write_function'] = True

        return record

class account_register_payments(models.TransientModel):
    _inherit = 'account.register.payments'

    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        amount = self._compute_payment_amount(invoices=invoices) if self.multi else self.amount
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        bank_account = self.multi and invoices[0].partner_bank_id or self.partner_bank_account_id
        pmt_communication = self.show_communication_field and self.communication \
                            or self.group_invoices and ' '.join([inv.reference or inv.number for inv in invoices]) \
                            or invoices[0].reference # in this case, invoices contains only one element, since group_invoices is False
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': pmt_communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': bank_account.id,
            'multi': False,
            'payment_difference_handling': self.payment_difference_handling,
            'writeoff_account_id': self.writeoff_account_id.id,
            'writeoff_label': self.writeoff_label,
        }

        return values

class hide_state_code(models.Model):
    _inherit = 'res.country.state'

    @api.multi
    def name_get(self):
        # super(hide_state_code,self).name_get()
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result