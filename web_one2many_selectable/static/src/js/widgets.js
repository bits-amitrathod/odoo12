odoo.define('web_one2many_selectable.form_widgets', function (require) {
"use strict";

/**
 * This file defines a client action that opens in a dialog (target='new') and
 * allows the user to change his password.
 */
var core = require('web.core');
var AbstractField = require('web.AbstractField');
var Widget = require('web.Widget');
var web_client = require('web.web_client');
var fieldRegistry = require('web.field_registry');
var FieldOne2Many=fieldRegistry.get("one2many");
var _t = core._t;
var One2ManySelectable = FieldOne2Many.extend({
    template: "One2ManySelectable",
/**
     * @fixme: weird interaction with the parent for the $buttons handling
     *
     * @override
     * @returns {Deferred}
     */

    events: {
        "click .cf_button_confirm": "action_selected_lines",
    },
    start: function () {
        //console.log("inside start");
        this._super.apply(this, arguments);
        var result=this._super.apply(this, arguments);
    	return result;
    },

   _render: function () {
          this._super.apply(this, arguments);
          if(!this.renderer.hasSelectors){
            this.renderer.hasSelectors=true;
          }
   },
    action_selected_lines: function(e)
	{
			var self=this;
			var ids=[];
			var flag=false
			var records=this.recordData.prioritization_ids.data

			var selected_ids = this.renderer.selection;
			if (selected_ids.length === 0)
			{
				this.do_warn(_t("You must choose at least one record."));
				return false;
			}

            //console.log(records)
            selected_ids.forEach(function(seletedId) {
             //console.log(seletedId);
              records.forEach(function(record) {

                    if(record.id==seletedId){
                        //console.log("Inside If");
                        //console.log(record.res_id);
                        if(record.res_id===undefined){
                                //console.log("Inside If1");
                                flag=true
                                //this.do_warn(_t("You must save the record before Copy Down."));
				            //return false;
                        }else{
                             //console.log("Inside else");
                             ids.push(record.res_id);
                        }

			        }
              });
            });
            if (flag)
			{
				this.do_warn(_t("You must save the record before Multiple Update."));
				return false;
			}
            e.preventDefault();
            var returnVal=this.do_action({
                name: _t("Multiple Update"),
                type: "ir.actions.act_window",
                res_model: "prioritization.transient",
                domain : [],
                views: [[false, "form"]],
                target: 'new',
                context: {'selected_ids':ids},
                view_type : 'form',
                view_mode : 'form'
            });
		},
});

fieldRegistry.add("one2many_selectable", One2ManySelectable);
return One2ManySelectable;

});