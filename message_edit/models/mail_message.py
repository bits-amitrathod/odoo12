# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class mail_message(models.Model):
    _name = 'mail.message'
    _inherit = 'mail.message'

    changed = fields.Boolean('Changed', default=False)
    history_ids = fields.One2many(
        'message.edit.history',
        'message_id',
        'History',
    )

    def write(self, values):
        """
        Overwrite to add checks in case of message editing

        Extra info:
         * check for empty values is not required, since in such a case write would not be launched
        """
        if self._context.get('message_edit'):
            if not self.env.user.has_group("message_edit.group_message_editing_superuser"):
                current_partner = self.env.user.partner_id.id
                if current_partner != values.get("author_id") and current_partner != self.sudo().author_id.id:
                    raise UserError(_(u'Only the author of the message can edit it.'),)
            old_message = {
                'name': self.subject,
                'body': self.body,
                'update_date': fields.Datetime.now(),
            }
            values['history_ids'] = [(0, 0, old_message)]
            values['changed'] = True
        return super(mail_message, self).write(values)

    def message_format(self, format_reply=True):
        """
        Overwrite to pass 'changed' and whether message is activity

        Returns:
         * list of dicts per each message in the format for web client
        """
        message_values = super(mail_message, self).message_format(format_reply=format_reply)
        guaranteed_subtypes = self.env.ref("mail.mt_activities") + self.env.ref("mail.mt_comment")
        for mes_value in message_values:
            message = self.browse(mes_value.get("id"))
            mes_value.update({
                "changed": message.changed,
                "editable_subtype": mes_value['subtype_id'] and mes_value['subtype_id'][0] in guaranteed_subtypes.ids,
            })
        return message_values

    def action_edit_message_thread(self):
        """
        Dummy method used for auto message form closure but to execute write
        """
        pass
