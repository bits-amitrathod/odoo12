odoo.define('in_stock_report_button', function (require) {
"use strict";

var core = require('web.core');
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
                error: (error) => this.call('crash_manager', 'rpc_error', error),
                success: function(){
                    console.log("------------aa-----------")
                    framework.unblockUI()
                }
            })

        }

    });

})



///** @odoo-module */
//
//import { registry } from '@web/core/registry';
//
//import { listView } from '@web/views/list/list_view';
//import { ListController } from '@web/views/list/list_controller';
//
////import { useArchiveEmployee } from '@hr/views/archive_employee_hook';
//
//export class SPSCustomListController extends ListController {
//    setup() {
//        super.setup();
//        this.archiveEmployee = useArchiveEmployee();
//    }
//
//    getActionMenuItems() {
//        const menuItems = super.getActionMenuItems();
//        const selectedRecords = this.model.root.selection;
//
//        // Only override the Archive action when only 1 record is selected.
//        if (!this.archiveEnabled || selectedRecords.length > 1 || !selectedRecords[0].data.active) {
//            return menuItems;
//        }
//
//        const archiveAction = menuItems.other.find((item) => item.key === "archive");
//        if (archiveAction) {
//            archiveAction.callback = this.archiveEmployee.bind(this, selectedRecords[0].resId);
//        }
//        return menuItems;
//    }
//}
//
//registry.category('views').add('hr_employee_list', {
//    ...listView,
//    Controller: EmployeeListController,
//});