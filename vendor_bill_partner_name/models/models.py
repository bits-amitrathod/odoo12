
from odoo import models, fields, api, _,tools
import base64
import threading
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date
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
        help="Used to select automatically the right address according to the context in sales and purchases documents.",
        track_visibility='onchange')

    #@api.multi
    # def name_get(self):
    #
    #     res = []
    #     for partner in self:
    #         name = partner.name or ''
    #         name1 = ""
    #         if (self.env.context.get('vendor_bill_partner_name_display_name') and "supplier" == self.env.context.get('res_partner_search_mode')):
    #         # or\
    #         #     (self.env.context.get('sale_invoice_sipping_partner_name_display_name') and True != ('show_address_only' in self._context ))   or\
    #         #         (self.env.context.get('sale_invoice_partner_name_display_name') and True != ('show_address_only' in self._context ) ) \
    #
    #             if partner.company_name or partner.parent_id:
    #                 if not name and partner.type in ['invoice', 'delivery', 'other','ap']:
    #                     name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
    #                 if not partner.is_company:
    #                     if partner.type :
    #                         if partner.type == 'other' and partner.company_type == 'company':
    #                             typ = 'AP'
    #                             name = "%s :- %s ,%s" % (typ,
    #                                                      partner.parent_id.name or partner.name,
    #                                                      name)
    #                         else:
    #                             name = "%s :- %s ,%s" % ((partner.type).upper(),
    #                                                      partner.commercial_company_name or partner.parent_id.name,
    #                                                      name)
    #                 else:
    #                     if partner.type:
    #                         if partner.type == 'other' and partner.company_type == 'company':
    #                             typ = 'AP'
    #                             name = "%s :- %s ,%s" % (typ,
    #                                                      partner.parent_id.name or partner.name,
    #                                                      name)
    #                         else:
    #                             name = "%s :- %s ,%s" % ((partner.type).upper(),
    #                                                      partner.commercial_company_name or partner.parent_id.name,
    #                                                      name)
    #
    #             else:
    #                 if partner.type:
    #                     name = "%s :- %s" % (('main').upper(),
    #                                           partner.commercial_company_name or partner.name)
    #         else:
    #             if partner.company_name or partner.parent_id:
    #                 if not name and partner.type in ['invoice', 'delivery', 'other','ap']:
    #                     name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
    #                 if not partner.is_company:
    #                     name = "%s ,%s" % (partner.commercial_company_name or partner.parent_id.name, name)
    #                 else:
    #                     if partner.is_company and partner.company_type == 'company':
    #                             typ = 'AP'
    #                             name = "%s :- %s ,%s" % (typ,partner.parent_id.name or partner.name,name)
    #                     else:
    #                         name = "%s ,%s" % (partner.commercial_company_name or partner.parent_id.name, name)
    #
    #         if self._context.get('show_address_only'):
    #             name = partner._display_address(without_company=True)
    #         if self._context.get('show_address'):
    #             name = name + "\n" + partner._display_address(without_company=True)
    #         name = name.replace('\n\n', '\n')
    #         name = name.replace('\n\n', '\n')
    #         if self._context.get('show_email') and partner.email:
    #             name = "%s <%s>" % (name, partner.email)
    #         if self._context.get('html_format'):
    #             name = name.replace('\n', '<br/>')
    #         res.append((partner.id, name))
    #     return res
    #
    # @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name')
    # def _compute_display_name(self):
    #     diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
    #     names = dict(self.with_context(**diff).name_get())
    #     for partner in self:
    #         p_name = names.get(partner.id)
    #         if p_name.startswith("AP :-"):
    #             partner.display_name = p_name[5:]
    #         else:
    #             partner.display_name = names.get(partner.id)
    # #@api.multi
    # def write(self, vals):
    #     super_return = super(VendorBillPartnerName, self).write(vals)
    #
    #     colorize, img_path, image = False, False, False
    #
    #     if self.type in ['other']:
    #         img_path = get_module_resource('vendor_bill_partner_name', 'static/src/img', 'cart.png')
    #         colorize = True
    #
    #     if not image and self.type == 'invoice':
    #         img_path = get_module_resource('base', 'static/img', 'money.png')
    #     elif not image and self.type == 'delivery':
    #         img_path = get_module_resource('base', 'static/img', 'truck.png')
    #     elif not image and self.is_company:
    #         img_path = get_module_resource('base', 'static/img', 'company_image.png')
    #     elif not image:
    #         img_path = get_module_resource('base', 'static/img', 'avatar.png')
    #         colorize = True
    #
    #     if img_path:
    #         with open(img_path, 'rb') as f:
    #             image = f.read()
    #     if image and colorize:
    #         self.image = tools.image_colorize(image)
    #     tools.image_resize_image_big(base64.b64encode(image))

    # @api.multi
    def name_get(self):

        res = []
        for partner in self:
            name = partner.name or ''
            if (self.env.context.get('vendor_bill_partner_name_display_name')):
            # and "supplier" == self.env.context.get(
            #         'res_partner_search_mode')):
                # or\
                #     (self.env.context.get('sale_invoice_sipping_partner_name_display_name') and True != ('show_address_only' in self._context ))   or\
                #         (self.env.context.get('sale_invoice_partner_name_display_name') and True != ('show_address_only' in self._context ) ) \

                if partner.company_name or partner.parent_id:
                    if not name and partner.type in ['invoice', 'delivery', 'other', 'ap']:
                        name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                    if not partner.is_company:
                        if partner.type:
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
                    if not name and partner.type in ['invoice', 'delivery', 'other', 'ap']:
                        name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                    if not partner.is_company:
                        name = "%s ,%s" % (partner.commercial_company_name or partner.parent_id.name, name)

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



# class account_move(models.Model):
#     _inherit = "account.move"
#
#     @api.model
#     def create(self, values):
#         # Override the original create function for the res.partner model
#         record = super(account_move, self).create(values)
#
#         # Change the values of a variable in this super function
#         # record['passed_override_write_function'] = True
#
#         return record

# class account_register_payments(models.TransientModel):
#     _inherit = 'account.register.payments'
#
#     #@api.multi
#     def _prepare_payment_vals(self, invoices):
#         '''Create the payment values.
#
#         :param invoices: The invoices that should have the same commercial partner and the same type.
#         :return: The payment values as a dictionary.
#         '''
#         amount = self._compute_payment_amount(invoices=invoices) if self.multi else self.amount
#         payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
#         bank_account = self.multi and invoices[0].partner_bank_id or self.partner_bank_account_id
#         pmt_communication = self.show_communication_field and self.communication \
#                             or self.group_invoices and ' '.join([inv.reference or inv.number for inv in invoices]) \
#                             or invoices[0].reference # in this case, invoices contains only one element, since group_invoices is False
#         values = {
#             'journal_id': self.journal_id.id,
#             'payment_method_id': self.payment_method_id.id,
#             'payment_date': self.payment_date,
#             'communication': pmt_communication,
#             'invoice_ids': [(6, 0, invoices.ids)],
#             'payment_type': payment_type,
#             'amount': abs(amount),
#             'currency_id': self.currency_id.id,
#             'partner_id': invoices[0].partner_id.id,
#             'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
#             'partner_bank_account_id': bank_account.id,
#             'multi': False,
#             'payment_difference_handling': self.payment_difference_handling,
#             'writeoff_account_id': self.writeoff_account_id.id,
#             'writeoff_label': self.writeoff_label,
#         }
#
#         return values

class hide_state_code(models.Model):
    _inherit = 'res.country.state'

    #@api.multi
    def name_get(self):
        # super(hide_state_code,self).name_get()
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result


class AccountMoveVendorBill(models.Model):
    _inherit = "account.move"

    due_date_note = fields.Text(string="Due Dates", compute="due_date_note_cal")
    def create(self, vals_list):
        data = super(AccountMoveVendorBill, self).create(vals_list)
        if self.env.context.get('create_bill'):
            res_partner = data.partner_id
            for obj in res_partner:
                if obj.is_parent:
                    for child_id in obj.child_ids:
                        if child_id.type == "other":
                            data.partner_id = child_id.id
                else:
                    for child_id in obj.parent_id.child_ids:
                        if child_id.type == "other":
                            data.partner_id = child_id.id
        return data

    @api.onchange('invoice_payment_term_id')
    @api.depends('invoice_payment_term_id')
    def due_date_note_cal(self):
        for rec in self:
            lista = list(rec.invoice_payment_term_id.line_ids)
            date_ref = rec.invoice_date or fields.Date.context_today(rec)
            rec.due_date_note = False
            due_str = ""
            for line in lista:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                    if line.day_of_the_month > 0:
                        months_delta = (line.day_of_the_month < next_date.day) and 1 or 0
                        next_date += relativedelta(day=line.day_of_the_month, months=months_delta)
                elif line.option == 'after_invoice_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'day_following_month':
                    next_date += relativedelta(day=line.days, months=1)
                elif line.option == 'day_current_month':
                    next_date += relativedelta(day=line.days, months=0)
                due_str += "Due Date :- " + str(format_date(rec.env, next_date, date_format="MM/dd/yyyy")) + "\n"

            if due_str == "":
                rec.due_date_note = "Due Date :- " + str(
                    format_date(rec.env, rec.invoice_date_due, date_format="MM/dd/yyyy"))
            else:
                rec.due_date_note = due_str

