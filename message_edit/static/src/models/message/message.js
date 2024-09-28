odoo.define('message_edit/static/src/models/message/message.js', function (require) {
'use strict';

    const { 
        registerInstancePatchModel,
        registerClassPatchModel,
        registerFieldPatchModel,
    } = require('mail/static/src/model/model_core.js');
    const { attr, } = require('mail/static/src/model/model_field.js');

    registerClassPatchModel('mail.message', 'message_edit/static/src/models/message/message.js', {
        /**
         * Re-write to pass data important for widget
         */
        convertData(data) {
            const data2 = this._super(data);
            if ('changed' in data) {data2.messageEditChanged = data.changed};
            if ('editable_subtype' in data) {data2.editableSubtype = data.editable_subtype};     
            return data2
        },
    });

    registerInstancePatchModel('mail.message', 'message_edit/static/src/models/message/message.js', {
        /**
         * Open message edit dialog and reload component on close
         */
        editMessage() {
            const action = {
                name: this.env._t("Edit Message"),
                type: 'ir.actions.act_window',
                res_model: 'mail.message',
                views: [[false, 'form']],
                target: 'new',
                res_id: this.id,
                context: {
                    'form_view_ref': 'message_edit.mail_message_edit_view_form',
                    'message_edit': true,
                },
            };
            this.env.bus.trigger('do-action', {
                action,
                options: {on_close: () => this.fetchAndUpdateAfterEdit()},
            });
        },
        /**
         * Get new message values by rpc and convert data
         */
        async fetchAndUpdateAfterEdit() {
            const [data] = await this.async(() => this.env.services.rpc({
                model: 'mail.message',
                method: 'message_format',
                args: [[this.id]],
            }));
            this.update(this.constructor.convertData(data));
        },
    });

    registerFieldPatchModel('mail.message', 'message_edit/static/src/models/message/message.js', {
        /**
         * Whether this message was already changed
         */
        messageEditChanged: attr({
            default: false,
        }),
        /**
         * Whether this message is an activity
         */
        editableSubtype: attr({
            default: false,
        }),
    });

});
        