# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.addons.http_routing.models.ir_http import slugify, _guess_mimetype

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # website_expiration_date = fields.Boolean(string='Lot expiration dates', default_model='res.config.settings')
    website_expiration_date = fields.Boolean(string='Lot expiration dates')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            website_expiration_date=get_param('website_sales.website_expiration_date')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('website_sales.website_expiration_date', self.website_expiration_date)


class Website(models.Model):
    _inherit = "website"

    def _prepare_sale_order_values(self, partner, pricelist):
        values = super(Website, self)._prepare_sale_order_values(partner, pricelist)
        address = partner.address_get(['invoice'])
        if address['invoice']:
            values['partner_invoice_id'] = address['invoice']
        return values

    @api.model
    def new_page_test(self, name=False, add_menu=False, template='website.default_page', ispage=True, namespace=None):
        """ Create a new website page, and assign it a xmlid based on the given one
            :param name : the name of the page
            :param template : potential xml_id of the page to create
            :param namespace : module part of the xml_id if none, the template module name is used
        """
        if namespace:
            template_module = namespace
        else:
            template_module, _ = template.split('.')
        page_url = '/' + slugify(name, max_length=1024, path=True)
        page_url = self.get_unique_path(page_url)
        page_key = slugify(name)
        result = dict({'url': page_url, 'view_id': False})

        if not name:
            name = 'Home'
            page_key = 'home'

        template_record = self.env.ref(template)
        website_id = self._context.get('website_id')
        key = self.get_unique_key(page_key, template_module)
        view = template_record.copy({'website_id': website_id, 'key': key})

        view.with_context(lang=None).write({
            'arch': template_record.arch.replace(template, key),
            'name': name,
        })

        if view.arch_fs:
            view.arch_fs = False

        website = self.get_current_website()
        if ispage:
            page = self.env['website.page'].create({
                'url': page_url,
                'website_id': website.id,  # remove it if only one webiste or not?
                'view_id': view.id,
            })
            result['view_id'] = view.id

        _logger.info('------- start -----------')
        _logger.info('template_record :')

        if add_menu:
            self.env['website.menu'].create({
                'name': name,
                'url': page_url,
                'parent_id': website.menu_id.id,
                'page_id': page.id,
                'website_id': website.id,
            })
        return result
