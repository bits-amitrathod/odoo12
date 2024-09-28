odoo.define('prioritization_engine.ActionManager', function (require) {
"use strict";
/* TODO: UPG ODOO16 NOTE require('web.ActionManager');  this Is   Deprecated  */
var ActionManager = require('web.ActionManager');
    ActionManager.include({
        ir_actions_act_close_wizard_and_reload_view: function (action, options) {
            if (!this.dialog) {
                options.on_close();
            }
            this.dialog_stop();
            this.inner_widget.views['form'].controller.reload();
            return $.when();
        },
    });
return ActionManager;
});