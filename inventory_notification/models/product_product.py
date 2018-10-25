from odoo import api, fields, models, tools, _



class ProductNotification(models.Model):
    _inherit = "product.product"
    notification_date=fields.Datetime('Last Message Date', help='Date of the notification send to sales team.')


