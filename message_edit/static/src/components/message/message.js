odoo.define('message_edit/static/src/components/message/message.js', function (require) {
'use strict';

    const components = {
        Message: require('mail/static/src/components/message/message.js'),
    };
    const { patch } = require('web.utils');

    patch(components.Message, 'message_edit/static/src/components/message/message.js', {
        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onMessageEdit: function(ev) {
            ev.stopPropagation();
            this.message.editMessage()
        },
    });

});
