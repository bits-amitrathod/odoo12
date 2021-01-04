# -*- coding: utf-8 -*-
from odoo import api, models, fields

class WebResource(models.Model):
    _name = 'resource.webresource'

    title = fields.Char(string='Resource Title', required=True)
    description = fields.Char(string='Resource Description', required=True)
    url = fields.Char(string='Resource URL', required=True)

    active = fields.Boolean(string='Active', default=True)
    website_published = fields.Boolean(string='website_published', default=False)

    @api.multi
    def toggle_website_published(self):
        ''' When clicking on the website publish toggle button, the website_published is reversed and
        the acquirer journal is set or not in favorite on the dashboard.
        '''
        self.ensure_one()
        self.website_published = not self.website_published
        # if self.journal_id:
        #     self.journal_id.show_on_dashboard = self.website_published
        return True