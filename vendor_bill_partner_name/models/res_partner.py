
import base64
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.modules import get_module_resource

class VendorBillPartnerName(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(selection_add=
        [('contact', 'Contact'),
         ('invoice', 'Invoice address'),
         ('delivery', 'Shipping address'),
         ('other', 'AP Address'),
         # ('private', 'Private Address'),
         # ('ap', 'AP Address'),
         ], string='Address Type',
        default='contact',
        help="Used to select automatically the right address according to the context in sales and purchases documents.",
        tracking=True)

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


