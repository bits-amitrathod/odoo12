from odoo import models, fields, api, _ , Command


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        """ - mass_mailing: we cannot render, so return the template values
            - normal mode: return rendered values
            /!\ for x2many field, this onchange return command instead of ids
        """
        if template_id and composition_mode == 'mass_mail':
            template = self.env['mail.template'].browse(template_id)
            values = dict(
                (field, template[field])
                for field in ['subject', 'body_html',
                              'email_from',
                              'reply_to',
                              'mail_server_id']
                if template[field]
            )
            if template.attachment_ids:
                values['attachment_ids'] = [att.id for att in template.attachment_ids]
            if template.mail_server_id:
                values['mail_server_id'] = template.mail_server_id.id
        elif template_id:
            values = self.generate_email_for_composer(
                template_id, [res_id],
                ['subject', 'body_html',
                 'email_from',
                 'email_cc', 'email_to', 'partner_to', 'reply_to',
                 'attachment_ids', 'mail_server_id'
                ]
            )[res_id]
            # transform attachments into attachment_ids; not attached to the document because this will
            # be done further in the posting process, allowing to clean database if email not send
            attachment_ids = []
            Attachment = self.env['ir.attachment']
            for attach_fname, attach_datas in values.pop('attachments', []):
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                }
                attachment_ids.append(Attachment.create(data_attach).id)

            # adding shipping lebel attachment to the mail composer
            attachment = self.env['ir.attachment'].search(
                [('res_id', '=', res_id), ('res_model', '=', 'purchase.order'), ('name', 'like', '%FedEx%')],
                order="id desc")
            ship_label = attachment and attachment[0] or False
            if ship_label:
                attachment_ids.append(ship_label.id)

            if values.get('attachment_ids', []) or attachment_ids:
                values['attachment_ids'] = [Command.set(values.get('attachment_ids', []) + attachment_ids)]
        else:
            default_values = self.with_context(
                default_composition_mode=composition_mode,
                default_model=model,
                default_res_id=res_id
            ).default_get(['composition_mode', 'model', 'res_id', 'parent_id',
                           'subject', 'body',
                           'email_from',
                           'partner_ids', 'reply_to',
                           'attachment_ids', 'mail_server_id'
                          ])
            values = dict(
                (key, default_values[key])
                for key in ['subject', 'body',
                            'email_from',
                            'partner_ids', 'reply_to',
                            'attachment_ids', 'mail_server_id'
                           ] if key in default_values)

        if values.get('body_html'):
            values['body'] = values.pop('body_html')

        # This onchange should return command instead of ids for x2many field.
        values = self._convert_to_write(values)
        return {'value': values}

# Bellow code is copied form odoo 14 because odoo 16 has removed that code
#  and fields are using in custom views
class MailThreadInherit(models.AbstractModel):
    _inherit = 'mail.thread'

    message_unread = fields.Boolean(string='Unread Messages', compute='_get_message_unread', help="If checked, new messages require your attention.")


    def _get_message_unread(self):
        for record in self:
            record.message_unread = record.has_message




