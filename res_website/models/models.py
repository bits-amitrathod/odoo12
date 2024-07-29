# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools import image

class WebResource(models.Model):
    _name = 'resource.webresource'
    _description = "Web Resource"

    title = fields.Char(string='Resource Title', required=True)
    description = fields.Char(string='Resource Description', required=True)
    url = fields.Char(string='Resource URL', required=True)

    active = fields.Boolean(string='Active', default=True)
    website_published = fields.Boolean(string='website_published', default=False)


    category = fields.Selection([
        ('award', 'Awards and Achievements'),
        ('video', 'Video'),
    ], default='award', string='Category', required=True )

    image = fields.Binary('Image',attachment=True)
    image_medium = fields.Binary('Medium',  store=True, attachment=True)
    image_thumb = fields.Binary('Thumbnail', store=True, attachment=True)

    # @api.depends('image')
    # def _get_image(self):
    #     for record in self:
    #         if record.image:
    #             record.image_medium = image.crop_image(record.image, type='top', ratio=(4, 3), size=(500, 400))
    #             record.image_thumb = image.crop_image(record.image, type='top', ratio=(4, 3), size=(200, 200))
    #         else:
    #             record.image_medium = False
    #             record.iamge_thumb = False

    #@api.multi
    def toggle_website_published(self):
        ''' When clicking on the website publish toggle button, the website_published is reversed and
        the acquirer journal is set or not in favorite on the dashboard.
        '''
        self.ensure_one()
        self.website_published = not self.website_published
        # if self.journal_id:
        #     self.journal_id.show_on_dashboard = self.website_published
        return True