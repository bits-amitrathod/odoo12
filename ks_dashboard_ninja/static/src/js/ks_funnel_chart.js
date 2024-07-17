/** @odoo-module */

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { qweb } from 'web.core';
const { Component, onWillUnmount, onWillUpdateProps, useEffect, useRef, useState, onMounted, willStart } = owl;

export class ks_funnel_chart extends Component{
    setup(){
        var self =this;
        this.root =null;
        this.funnelRef = useRef("funnel");
        onMounted(() =>{
             this._Ks_render();
         })

        onWillUpdateProps(this.WillUpdateProps);
    }

    WillUpdateProps(){
        if(this.root){
            this.root.dispose();
        }
        this._Ks_render();
        }

    _Ks_render(){
        var self = this;
        var rec = this.props.record.data;
        var rec = this.props.record.data;
        if ($(self.funnelRef.el.parentElement).find("div.text").length){
            $(self.funnelRef.el.parentElement).find("div.text").remove();
        }
        if (rec.ks_dashboard_item_type === 'ks_funnel_chart'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Select Group By to create chart view"));
                    } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Select Measure and Group By to create chart view"));
                        var h2Element = document.getElementById("text");
                        h2Element.textContent = " ";
                        var $ChartElement = $(document.getElementById("chartdiv"));
                        $ChartElement.hide();
                    } else if (!rec.ks_chart_data_count_type) {
                        $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Select Chart Data Count Type"));
                    } else {
                        var $ChartElement = $(document.getElementById("chartdiv"));
                        $ChartElement.show();
                        this.get_funnel_chart(rec);
                    }
                } else {
                    $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Select a Model first."));
                    var $ChartElement = $(document.getElementById("chartdiv"));
                        $ChartElement.hide();
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        this.get_funnel_chart(rec);
                } else {
                    $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else {
                    $(self.funnelRef.el.parentElement).prepend($("<div class='text'>").text("Please run the appropriate Query"));
                     var h2Element = document.getElementById("text");
                     h2Element.textContent = " ";
            }

        }
    }

    get_funnel_chart(rec){

        if($(this.funnelRef.el).find(".funnel_text").length){
            $(this.funnelRef.el).find(".funnel_text").remove();
        }
        const chart_data = JSON.parse(this.props.record.data.ks_chart_data);
        if (chart_data.datasets && chart_data['labels']){
            if (rec.name) {
                this.ks_chart_name = rec.name;
            }
            else if (rec.ks_model_name) {
                this.ks_chart_name = rec.ks_model_id[1];
            }
            else{
                this.ks_chart_name = " ";
            }
            var h2Element = document.getElementById("text");
            h2Element.textContent = this.ks_chart_name;
        }
        var ks_labels = chart_data['labels'];
        var ks_data = chart_data.datasets[0].data;
        const ks_sortobj = Object.fromEntries(
            ks_labels.map((key, index) => [key, ks_data[index]]),
        );
        const keyValueArray = Object.entries(ks_sortobj);
        keyValueArray.sort((a, b) => b[1] - a[1]);

        var data=[];
        if (keyValueArray.length){
            for (let i=0 ; i<keyValueArray.length ; i++){
                data.push({"stage":keyValueArray[i][0],"applicants":keyValueArray[i][1]})
            }
            this.root = am5.Root.new(this.funnelRef.el);
            const theme = this.props.record.data.ks_funnel_item_color

            switch(theme){
            case "default":
                this.root.setThemes([am5themes_Animated.new(this.root)]);
                break;
            case "dark":
                this.root.setThemes([am5themes_Dataviz.new(this.root)]);
                break;
            case "material":
                this.root.setThemes([am5themes_Material.new(this.root)]);
                break;
            case "moonrise":
                this.root.setThemes([am5themes_Moonrise.new(this.root)]);
                break;
            };

            var chart = this.root.container.children.push(
                am5percent.SlicedChart.new(this.root, {
                    layout: this.root.verticalLayout
                })
            );

                // Create series
            var series = chart.series.push(
                am5percent.FunnelSeries.new(this.root, {
                    alignLabels: false,
                    name: "Series",
                    valueField: "applicants",
                    categoryField: "stage",
                    orientation: "vertical",
                })
            );

            series.data.setAll(data);
            series.appear(1000);

            if(this.props.record.data.ks_show_data_value && this.props.record.data.ks_data_label_type=="value"){
                series.labels.template.set("text", "{category}: {value}");
            }else if(this.props.record.data.ks_show_data_value && this.props.record.data.ks_data_label_type=="percent"){
                series.labels.template.set("text", "{category}: {valuePercentTotal.formatNumber('0.00')}%");
            }else{
                series.ticks.template.set("forceHidden", true);
//                series.labels.template.set("forceHidden", true);
            }

            var legend = chart.children.push(am5.Legend.new(this.root, {
                centerX: am5.p50,
                x: am5.p50,
                marginTop: 15,
                marginBottom: 15,
                layout: this.root.horizontalLayout,
            }));

            if(this.props.record.data.ks_hide_legend==true){
                legend.data.setAll(series.dataItems);
            }

            chart.appear(1000, 100);
        }else{
            $(this.funnelRef.el).append($("<div class='funnel_text'>").text("No Data Available."));
        }
    }
}

ks_funnel_chart.template = "ks_dashboard_ninja.ksfunnelchart";
ks_funnel_chart.supportedTypes = ["char"];


registry.category("fields").add("ks_funnel_chart", ks_funnel_chart);