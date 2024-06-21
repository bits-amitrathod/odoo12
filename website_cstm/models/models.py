# -*- coding: utf-8 -*-
from typing import Dict, Any

from odoo import models, fields, api
import logging
from odoo.addons.http_routing.models.ir_http import slugify, _guess_mimetype

_logger = logging.getLogger(__name__)

class website_cstm(models.Model):
    _name = 'website_cstm.product_instock_notify'

    email = fields.Char()
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', ondelete='cascade', required=True)
    status = fields.Selection([('pending', 'Pending'),('done', 'Done')])

    @api.model
    def send_email_product_instock(self):
        StockNotifcation = self.env['website_cstm.product_instock_notify'].sudo()
        subcribers = StockNotifcation.search([
            ('status', '=', 'pending'),
        ])
        notificationList = {}
        template = self.env.ref('website_cstm.mail_template_product_instock_notification_email')
        for subcriber in subcribers:
            if subcriber.product_tmpl_id.actual_quantity > 0:
                if not subcriber.email in notificationList :
                    notificationList[subcriber.email] = []
                notificationList[subcriber.email].append(subcriber)
                subcriber.status = 'done'

        for email in notificationList:
            products = notificationList[email]
            local_context = {'email': email,'products': products}
            template.with_context(local_context).send_mail(products[0].product_tmpl_id.id, raise_exception=True)


class website_product_download_catelog_cstm(models.Model):
    _name = 'website_cstm.product_download_catelog'

    file = fields.Binary('File')
    filename = fields.Char()
    status = fields.Selection([('active', 'active'),('inactive', 'Inactive')])

    @api.model
    def create(self, vals):
        self.setActive(vals)
        return super(website_product_download_catelog_cstm, self).create(vals)

    #@api.multi
    def write(self, vals):
        self.setActive(vals)
        return super(website_product_download_catelog_cstm, self).write(vals)

    def setActive(self,vals):
        if vals['status'] == 'active':
            self.env.cr.execute(
                "UPDATE website_cstm_product_download_catelog SET  status='inactive' WHERE status ='active'")



class Website(models.Model):
    _inherit = "website"

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

        if add_menu:
            self.env['website.menu'].create({
                'name': name,
                'url': page_url,
                'parent_id': website.menu_id.id,
                'page_id': page.id,
                'website_id': website.id,
            })
        return result
