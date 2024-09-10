/** @odoo-module **/

import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
//import { session } from "@web/session";
import { blockUI, unblockUI } from "web.framework";
var session = require('web.session');
var ajax = require('web.ajax');

export class InStockReportListController extends ListController {
    setup() {
        super.setup();
//        this.archiveEmployee = useArchiveEmployee();
    }
    onClickExport() {
        this.filter_button()
    }
    onError(error){
        console.log("------------aa-----------",error)
        var message = error.messages
        throw new Error(message);
    }
    filter_button() {
        console.log("------------343aa-----------")
        var self = this;
        blockUI();
        ajax.get_file({
            url: '/web/export/in_stock_report',
            complete: unblockUI,
            error: self.onError,
            success: function(){
                console.log("------------aa-----------")
                unblockUI()
            }
        })

    }
}

registry.category('views').add('in_stock_list', {
    ...listView,
    Controller: InStockReportListController,
    buttonTemplate: 'in_stock_report.buttons',
});

