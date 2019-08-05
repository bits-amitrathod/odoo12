odoo.define('customer_credit_note.ChatThread', function (require) {
"use strict";

var ChatThread = require('mail.ChatThread');
var core = require('web.core');
var time = require('web.time');

var QWeb = core.qweb;

function time_from_now(date) {
    if (moment().diff(date, 'seconds') < 45) {
        return _t("now");
    }
    return date.fromNow();
}

var ORDER = {
    ASC: 1,
    DESC: -1,
};


ChatThread.include({

    render: function (messages, options) {
        var self = this;
        var msgs = _.map(messages, this._preprocess_message.bind(this));
        if (this.options.display_order === ORDER.DESC) {
            msgs.reverse();
            msgs.sort( compare );
        }
        options = _.extend({}, this.options, options);


    function compare( a, b ) {
        if ( a.day < b.day ){
            return -1;
        }
        if ( a.day > b.day ){
            return 1;
        }
            return 0;
    }

        // Hide avatar and info of a message if that message and the previous
        // one are both comments wrote by the same author at the same minute
        // and in the same document (users can now post message in documents
        // directly from a channel that follows it)
        var prev_msg;
        _.each(msgs, function (msg) {
            if (!prev_msg || (Math.abs(msg.date.diff(prev_msg.date)) > 60000) ||
                prev_msg.message_type !== 'comment' || msg.message_type !== 'comment' ||
                (prev_msg.author_id[0] !== msg.author_id[0]) || prev_msg.model !== msg.model ||
                prev_msg.res_id !== msg.res_id) {
                msg.display_author = true;
            } else {
                msg.display_author = !options.squash_close_messages;
            }
            prev_msg = msg;
        });

        this.$el.html(QWeb.render('mail.ChatThread', {
            messages: msgs,
            options: options,
            ORDER: ORDER,
            date_format: time.getLangDatetimeFormat(),
        }));

        this.attachments = _.uniq(_.flatten(_.map(messages, 'attachment_ids')));

        _.each(msgs, function(msg) {
            var $msg = self.$('.o_thread_message[data-message-id="'+ msg.id +'"]');
            $msg.find('.o_mail_timestamp').data('date', msg.date);

            self.insert_read_more($msg);
        });

        if (!this.update_timestamps_interval) {
            this.update_timestamps_interval = setInterval(function() {
                self.update_timestamps();
            }, 1000*60);
        }
    },

    _preprocess_message: function (message) {
        var msg = _.extend({}, message);

        msg.date = moment.min(msg.date, moment());
        msg.hour = time_from_now(msg.date);

        var date = msg.date.format('YYYY-MM-DD');

        if(msg.is_note){
            msg.day = _t("Note");
        } else if (date === moment().format('YYYY-MM-DD')) {
            if(!msg.is_note){
                msg.day = _t("Today");
            }
        } else if (date === moment().subtract(1, 'days').format('YYYY-MM-DD')) {
            if(!msg.is_note){
                msg.day = _t("Yesterday");
            }
        } else if(!msg.is_note){
            msg.day = msg.date.format('LL');
        }

        if (_.contains(this.expanded_msg_ids, message.id)) {
            msg.expanded = true;
        }

        msg.display_subject = message.subject && message.message_type !== 'notification' && !(message.model && (message.model !== 'mail.channel'));
        msg.is_selected = msg.id === this.selected_id;
        return msg;
    },

});

return ChatThread;

});
