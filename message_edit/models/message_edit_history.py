# -*- coding: utf-8 -*-

from odoo import fields, models

class message_edit_history(models.Model):
    """
    Model to keep message changes
    """
    _name = 'message.edit.history'
    _description = 'Mail Message Edit History'

    name = fields.Char('Subject')
    body = fields.Html('Body')
    update_date = fields.Datetime('Update Date')
    message_id = fields.Many2one(
        'mail.message', 
        'Message', 
        ondelete="cascade",
    )
