/** @odoo-module **/

import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(FormViewDialog.prototype,"ks_dashboard_ninja", {
        setup(){
            onMounted(this._mounted)
            return this._super(...arguments);
        },
        _mounted(){
            if (this.props.context.ks_form_view == true){
                $(this.modalRef.el).addClass('ks_dn_create_chart')
            }

        },

    });
