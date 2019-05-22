odoo.define('in_stock_report_button', function (require) {
"use strict";

var core = require('web.core');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');

var ListController = require('web.ListController');

    ListController.include({

        renderButtons: function($node) {

        this._super.apply(this, arguments);

            if (this.$buttons) {
                let filter_button = this.$buttons.find('.o_list_export_button');
                filter_button && filter_button.click(this.proxy('filter_button'));
            }

        },



        filter_button: function () {
         console.log("------------343aa-----------")
            framework.blockUI();
           this.getSession().get_file({
                url: '/web/export/in_stock_report',
                complete: framework.unblockUI,
                error: crash_manager.rpc_error.bind(crash_manager),
                success: function(){
                    console.log("------------aa-----------")
                    framework.unblockUI()
                }
            })

        }

    });

})