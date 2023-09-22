from odoo import models, fields, api, modules, exceptions, _
from odoo.tools.misc import clean_context


class MailActivityNotesCustom(models.Model):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.activity'

    def generic_char_search(self, operator, value, field):
        partner_link = self.env['partner.link.tracker']
        if operator in ['=', '!=', 'like', 'ilike', 'not ilike', 'not like','>=','<=','<','>']:
            record = partner_link.search([(field, operator, value)], limit=None)
            return [('related_partner_activity', 'in', [a.partner_id.id for a in record])]
        else:
            return expression.FALSE_DOMAIN
    def pro_search_for_sales_activity_notes(self, operator, value):
        return self.generic_char_search(operator, value, 'sales_activity_notes')

    def pro_search_for_acq_activity_notes(self, operator, value):
        return self.generic_char_search(operator, value, 'acq_activity_notes')



    sales_activity_notes = fields.Html("Sales Activity Notes", store=False, compute="_compute_act_note_field",
                                       search="pro_search_for_sales_activity_notes", readonly=False)
    acq_activity_notes = fields.Html("Acquisition Activity Notes", store=False, compute="_compute_act_note_field",
                                     search="pro_search_for_acq_activity_notes", readonly=False)

    related_partner_activity = fields.Many2one('res.partner', string="Related Partner")

    activity_priority = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')], string='Priority', store=True)

    reference = fields.Reference(string='Related Document',
                                 selection='_reference_models')

    email = fields.Char(related="related_partner_activity.email", readonly=True, store=False)
    phone = fields.Char(related="related_partner_activity.phone", readonly=True, store=False)
    mobile = fields.Char(related="related_partner_activity.mobile", readonly=True, store=False)

    # studio field replacement
    tags = fields.Many2many(related="related_partner_activity.category_id", readonly=True, store=False)
    # related field id studio field need to change
    direct_line = fields.Char(related="related_partner_activity.x_studio_direct_line", readonly=True, store=False)
    time_zone = fields.Selection([
        ('est', 'EST'),
        ('cst', 'CST'),
        ('mst', 'MST'),
        ('pst', 'PST'),
        ('ast', 'AST'),
        ('hast', 'HAST')],related="related_partner_activity.time_zone", readonly=True, store=False)
    function = fields.Char(related="related_partner_activity.function", readonly=True, store=False)

    comment = fields.Html(string='Comments')

    ordered_online = fields.Boolean(related="related_partner_activity.x_studio_ordered_online", readonly=True,
                                      store=False)
    ordered_with_ghx = fields.Boolean(related="related_partner_activity.x_studio_ordered_with_ghx", readonly=True, store=False)

    fiscal_year_end = fields.Selection(related="related_partner_activity.fiscal_year_end", readonly=True,
                                    store=False)
    top_subspecialties1 = fields.Many2many(related="related_partner_activity.top_subspecialties1", readonly=True,
                                      store=False)

    connected_in_ghx = fields.Boolean(related="related_partner_activity.x_studio_connected_in_ghx", readonly=True,
                                           store=False)
    ordered_with_ghx = fields.Boolean(related="related_partner_activity.x_studio_ordered_with_ghx", readonly=True,
                                           store=False)
    email_opt_out = fields.Boolean(related="related_partner_activity.email_opt_out", readonly=True,
                                        store=False)

    #date_done = fields.Date("Completed Date", index=True, readonly=False)

    # def write(self, vals):
    #     res = super().write(vals)
    #     return res

    @api.model
    def _reference_models(self):

        # models = self.env['ir.model'].sudo().search([('state', '!=', 'manual'), ('name', 'not in', model_list),
        #                                              ('name', 'not like', 'report'), ('name', 'not like', 'popup'),
        #                                              ('name', 'not like', 'Test'), ('name', 'not like', 'Tests'),
        #                                              ('name', 'not like', 'sps'), ('name', 'not like', 'prioritization'),
        #                                              ('name', 'not like', 'Tests')])

        model_list = ['Contact', 'Sales Order', 'Vendor Offer Automation', 'Lead/Opportunity']
        models = self.env['ir.model'].sudo().search([('state', '!=', 'manual'), ('name', 'in', model_list)])
        res = [(model.model, model.name)
               for model in models
               if not model.model.startswith('ir.')]
        return res


    def _compute_act_note_field(self):
        for record in self:
            # record.res_model = 'res.partner'
            # record.reference = 'res.partner,1'
            if record.related_partner_activity:
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes
            # studio field data migration
            record.comment = record.comment if record.comment else record.x_studio_comments

    @api.model
    def create(self, val):
        if val['res_model_id'] == False:
            val['res_model_id'] = self.env['ir.model'].sudo().search([('model', '=', 'res.partner')], limit=1).id
        record = super(MailActivityNotesCustom, self).create(val)
        popup_context = self.env.context.get('default_res_model')
        popup_model_id = self.env.context.get('default_res_id')
        if popup_context == 'res.partner' and popup_model_id:
            record.reference = self.env['res.partner'].search([('id', '=', popup_model_id)], limit=1)
        return record

    @api.onchange('acq_activity_notes', 'sales_activity_notes')
    def onchange_notes_fields(self):
        for record in self:
            popup_context = self.env.context.get('default_res_model')
            # if popup_context == 'res.partner' and record.related_partner_activity.id is False:
            #     record.related_partner_activity = self.env['res.partner'].search([('id', '=', record.res_id)], limit=1)
            if record.reference is None:
                if record.res_id:
                    record.reference = 'res.partner,'+str(record.res_id)+''
            if record.related_partner_activity:
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    if popup_context == 'res.partner':
                        if record.sales_activity_notes:
                            if record.sales_activity_notes != '<p><br/></p>':
                                partner_link.sales_activity_notes = record.sales_activity_notes
                        else:
                            record.sales_activity_notes = partner_link.sales_activity_notes

                        if record.acq_activity_notes:
                            if record.acq_activity_notes != '<p><br/></p>':
                                partner_link.acq_activity_notes = record.acq_activity_notes
                        else:
                            record.acq_activity_notes = partner_link.acq_activity_notes
                    else:
                        partner_link.sales_activity_notes = record.sales_activity_notes
                        partner_link.acq_activity_notes = record.acq_activity_notes
                else:
                    self.env['partner.link.tracker'].create({'partner_id': record.related_partner_activity.id,
                                                             'sales_activity_notes': record.sales_activity_notes,
                                                             'acq_activity_notes': record.acq_activity_notes })

    @api.onchange('related_partner_activity')
    def onchange_contact(self):
        for record in self:
            if record.related_partner_activity:
                # record.res_name = record.related_partner_activity.name
                # record.res_id = record.related_partner_activity.id
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes

    # Overwritten because Client Does Not want Notes overridden
    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            if self.activity_type_id.summary:
                self.summary = self.activity_type_id.summary
            self.date_deadline = self._calculate_date_deadline(self.activity_type_id)
            self.user_id = self.activity_type_id.default_user_id or self.env.user
            # if self.activity_type_id.default_description:
            #     self.note = self.activity_type_id.default_description

    # Overwritten because Client Does Not want Pop Up
    def action_done(self):
        self.state = 'done'
        self.active = False
        self.activity_done = True
        self.date_done = fields.Date.today()
        self.feedback = ''
        self._compute_state()
        messages = self.env['mail.message']
        record = self.env[self.res_model].sudo().browse(self.res_id)
        record.sudo().message_post_with_view(
            'mail.message_activity_done',
            values={
                'activity': self,
                'feedback': '',
                'display_assignee': self.user_id != self.env.user
            },
            subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
            mail_activity_type_id=self.activity_type_id.id,
        )
        messages |= record.sudo().message_ids[0]

    def action_view_activity_popup(self):
        self.ensure_one()
        view_id = self.env.ref(
            'sh_activities_management.sh_mail_activity_view_form_n').id
        return {
            'name': _('Schedule an Activity'),
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(view_id, 'form')],
            'res_id': self.id,
            'type': 'ir.actions.act_window'
        }

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(MailActivityNotesCustom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                submenu=submenu)
    #     res.res_model = 'res.partner'
    #     return res

    # @api.model
    # def create(self, values):
    #     # activity = super(MailActivityNotesCustom, self).create(values)
    #     activity = super(models.Model, self).create(values)
    #     need_sudo = False
    #     try:  # in multicompany, reading the partner might break
    #         partner_id = activity.user_id.partner_id.id
    #     except exceptions.AccessError:
    #         need_sudo = True
    #         partner_id = activity.user_id.sudo().partner_id.id
    #
    #     # send a notification to assigned user; in case of manually done activity also check
    #     # target has rights on document otherwise we prevent its creation. Automated activities
    #     # are checked since they are integrated into business flows that should not crash.
    #     if activity.user_id != self.env.user:
    #         if not activity.automated:
    #             activity._check_access_assignation()
    #         # if not self.env.context.get('mail_activity_quick_update', False):
    #         #     if need_sudo:
    #         #         activity.sudo().action_notify()
    #         #     else:
    #         #         activity.action_notify()
    #
    #     self.env[activity.res_model].browse(activity.res_id).message_subscribe(partner_ids=[partner_id])
    #     if activity.date_deadline <= fields.Date.today():
    #         self.env['bus.bus'].sendone(
    #             (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
    #             {'type': 'activity_updated', 'activity_created': True})
    #     return activity
    #
    # def write(self, values):
    #     if values.get('user_id'):
    #         user_changes = self.filtered(lambda activity: activity.user_id.id != values.get('user_id'))
    #         pre_responsibles = user_changes.mapped('user_id.partner_id')
    #     # res = super(MailActivityNotesCustom, self).write(values)
    #     res = super(models.Model, self).write(values)
    #
    #     # if values.get('user_id'):
    #     #     if values['user_id'] != self.env.uid:
    #     #         to_check = user_changes.filtered(lambda act: not act.automated)
    #     #         to_check._check_access_assignation()
    #     #         if not self.env.context.get('mail_activity_quick_update', False):
    #     #             user_changes.action_notify()
    #     #     for activity in user_changes:
    #     #         self.env[activity.res_model].browse(activity.res_id).message_subscribe(
    #     #             partner_ids=[activity.user_id.partner_id.id])
    #     #         if activity.date_deadline <= fields.Date.today():
    #     #             self.env['bus.bus'].sendone(
    #     #                 (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
    #     #                 {'type': 'activity_updated', 'activity_created': True})
    #     #     for activity in user_changes:
    #     #         if activity.date_deadline <= fields.Date.today():
    #     #             for partner in pre_responsibles:
    #     #                 self.env['bus.bus'].sendone(
    #     #                     (self._cr.dbname, 'res.partner', partner.id),
    #     #                     {'type': 'activity_updated', 'activity_deleted': True})
    #     return res
    #
    # def unlink(self):
    #     pass
    #     # for activity in self:
    #     #     if activity.date_deadline <= fields.Date.today():
    #     #         self.env['bus.bus'].sendone(
    #     #             (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
    #     #             {'type': 'activity_updated', 'activity_deleted': True})
    #     # return super(MailActivityNotesCustom, self).unlink()

    def action_done_duplicate_act(self):
        for activity_id in self:
            copy_of_activity = self.copy()

            activity_id.state = 'done'
            activity_id.active = False
            activity_id.date_done = fields.Date.today()
            activity_id.feedback = self.feedback
            activity_id.activity_done = True
            activity_id._compute_state()
            messages = self.env['mail.message']
            record = self.env[activity_id.res_model].sudo().browse(activity_id.res_id)
            record.sudo().message_post_with_view(
                'mail.message_activity_done',
                values={
                    'activity': activity_id,
                    'feedback': self.feedback,
                    'display_assignee': activity_id.user_id != self.env.user
                },
                subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
                mail_activity_type_id=activity_id.activity_type_id.id,
            )
            messages |= record.sudo().message_ids[0]

            view_id = self.env.ref(
                'sh_activities_management.sh_mail_activity_view_form_n').id
            if copy_of_activity:
                context = dict(self.env.context)
                context['form_view_initial_mode'] = 'edit'
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.activity',
                    'res_id': copy_of_activity.id,
                    'views': [(view_id, 'form')],
                    'context': context,
                }

    def action_done_duplicate_act_popup(self, feedback=False):
        ctx = dict(
            clean_context(self.env.context),
            default_previous_activity_type_id=self.activity_type_id.id,
            activity_previous_deadline=self.date_deadline,
            default_res_id=self.res_id,
            default_res_model=self.res_model,
        )
        copy_of_activity = self.copy()
        messages, next_activities = self._action_done(feedback=feedback)  # will unlink activity, dont access self after that
        # if next_activities:
        #     return False
        return {
            'name': _('Schedule an Activity'),
            'context': ctx,
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'res_id': copy_of_activity.id,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def write(self, vals):
        if self:
            for rec in self:
                if 'sh_user_ids' in vals :
                    if 'res_id' in vals and vals['res_id'] == 0:
                        del vals['res_id']

                    if 'related_partner_activity' in vals and not vals['related_partner_activity']:
                        del vals['related_partner_activity']
        return super(MailActivityNotesCustom, self).write(vals)


class MailThreadExtendCRM(models.AbstractModel):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.thread'

    @api.model_create_multi
    def create(self, vals_list):
        """ Chatter override :
            - subscribe uid
            - subscribe followers of parent
            - log a creation message
        """
        threads = super(MailThreadExtendCRM, self).create(vals_list)
        return threads

    def write(self, values):
        # Perform write
        result = super(MailThreadExtendCRM, self).write(values)
        return result

    def _message_auto_subscribe(self, updated_values, followers_existing_policy='skip'):
        """ Handle auto subscription. Auto subscription is done based on two
        main mechanisms

         * using subtypes parent relationship. For example following a parent record
           (i.e. project) with subtypes linked to child records (i.e. task). See
           mail.message.subtype ``_get_auto_subscription_subtypes``;
         * calling _message_auto_subscribe_notify that returns a list of partner
           to subscribe, as well as data about the subtypes and notification
           to send. Base behavior is to subscribe responsible and notify them;

        Adding application-specific auto subscription should be done by overriding
        ``_message_auto_subscribe_followers``. It should return structured data
        for new partner to subscribe, with subtypes and eventual notification
        to perform. See that method for more details.

        :param updated_values: values modifying the record trigerring auto subscription
        """
        if not self:
            return True

        new_partners, new_channels = dict(), dict()

        # return data related to auto subscription based on subtype matching (aka:
        # default task subtypes or subtypes from project triggering task subtypes)
        updated_relation = dict()
        child_ids, def_ids, all_int_ids, parent, relation = self.env['mail.message.subtype']._get_auto_subscription_subtypes(self._name)

        # check effectively modified relation field
        for res_model, fnames in relation.items():
            for field in (fname for fname in fnames if updated_values.get(fname)):
                updated_relation.setdefault(res_model, set()).add(field)
        udpated_fields = [fname for fnames in updated_relation.values() for fname in fnames if updated_values.get(fname)]

        if udpated_fields:
            # fetch "parent" subscription data (aka: subtypes on project to propagate on task)
            doc_data = [(model, [updated_values[fname] for fname in fnames]) for model, fnames in updated_relation.items()]
            res = self.env['mail.followers']._get_subscription_data(doc_data, None, None, include_pshare=True, include_active=True)
            for fid, rid, pid, cid, subtype_ids, pshare, active in res:
                # use project.task_new -> task.new link
                sids = [parent[sid] for sid in subtype_ids if parent.get(sid)]
                # add checked subtypes matching model_name
                sids += [sid for sid in subtype_ids if sid not in parent and sid in child_ids]
                if pid and active:  # auto subscribe only active partners
                    if pshare:  # remove internal subtypes for customers
                        new_partners[pid] = set(sids) - set(all_int_ids)
                    else:
                        new_partners[pid] = set(sids)
                if cid:  # never subscribe channels to internal subtypes
                    new_channels[cid] = set(sids) - set(all_int_ids)

        notify_data = dict()
        res = self._message_auto_subscribe_followers(updated_values, def_ids)
        for pid, sids, template in res:
            new_partners.setdefault(pid, sids)
            if template:
                partner = self.env['res.partner'].browse(pid)
                lang = partner.lang if partner else None
                notify_data.setdefault((template, lang), list()).append(pid)

        self.env['mail.followers']._insert_followers(
            self._name, self.ids,
            list(new_partners), new_partners,
            list(new_channels), new_channels,
            check_existing=True, existing_policy=followers_existing_policy)

        # notify people from auto subscription, for example like assignation
        for (template, lang), pids in notify_data.items():
            self.with_context(lang=lang)._message_auto_subscribe_notify(pids, template)

        return True

    def _message_auto_subscribe_notify(self, partner_ids, template):
        """ Notify new followers, using a template to render the content of the
        notification message. Notifications pushed are done using the standard
        notification mechanism in mail.thread. It is either inbox either email
        depending on the partner state: no user (email, customer), share user
        (email, customer) or classic user (notification_type)

        :param partner_ids: IDs of partner to notify;
        :param template: XML ID of template used for the notification;
        """
        if not self or self.env.context.get('mail_auto_subscribe_no_notify'):
            return
        if not self.env.registry.ready:  # Don't send notification during install
            return

        view = self.env['ir.ui.view'].browse(self.env['ir.model.data'].xmlid_to_res_id(template))

        for record in self:
            model_description = self.env['ir.model']._get(record._name).display_name
            values = {
                'object': record,
                'model_description': model_description,
                'access_link': record._notify_get_action_link('view'),
            }
            assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
            assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)
            # record.message_notify(
            #     subject=_('You have been assigned to %s', record.display_name),
            #     body=assignation_msg,
            #     partner_ids=partner_ids,
            #     record_name=record.display_name,
            #     email_layout_xmlid='mail.mail_notification_light',
            #     model_description=model_description,
            # )
