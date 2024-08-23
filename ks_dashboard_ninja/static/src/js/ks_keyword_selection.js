/** @odoo-module **/
import {registry} from "@web/core/registry";
import {useInputField} from "@web/views/fields/input_field_hook";
const {Component,useRef,useState,onWillStart} = owl;
import { qweb } from 'web.core';
var ajax = require('web.ajax');


export class KsKeywordSelection extends Component {
    static template = 'KsKeywordSelection';
    setup() {
        super.setup();
        this.props.record.data.ks_import_id;
        this.input = useRef('ks_input');
        this.search = useRef('ks_search');
        this.ks_sample_final_data = [];
        this.state = useState({ values: []});
        onWillStart(async()=>{
        this.ks_data_model = await ajax.jsonRpc('/web/dataset/call_kw', 'call',{
            model:'ks_dashboard_ninja.arti_int',
            method:'ks_get_keywords',
            args:[],
            kwargs: {},
        })
        this.state.values = this.ks_data_model

        });

    }


    _onKeyup(ev) {
        var value = ev.target.value;
        var self=this;
        var ks_active_target =  $(self.search.el).find(".active")
        if (value.length){
            var ks_value = value.toUpperCase();
            self.state.values =[];
            if (this.ks_data_model){
                this.ks_data_model.forEach((item) =>{
                    if (item.value.toUpperCase().indexOf(ks_value) >-1){
                        self.state.values.push(item)
                    }
                })
                self.state.values.splice(0,0,{"value":value,'id':0})
            }
        }else{
            this.state.values = this.ks_data_model
            $.each(ks_active_target, function(index,item) {
            $(item).removeClass("active")
            });
            this.props.update("")
        }


    }

   _onResponseSelect(ev) {
        var self = this;
        var value = $(ev.currentTarget).find(".ai-title")[0].textContent;
        self.props.update(value);
        self.input.el.value = value;
        var ks_active_target =  $(ev.currentTarget.parentElement).find(".active")
        $.each(ks_active_target, function(index,item) {
            $(item).removeClass("active")
         });
         if ($(ev.currentTarget).hasClass("generate-item") == false){
            $(ev.currentTarget).addClass("active")
         }

    }
}

registry.category("fields").add('ks_keyword_selection', KsKeywordSelection);