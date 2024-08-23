/** @odoo-module **/

/*global L*/

import { renderToString } from "@web/core/utils/render";
import { registry } from "@web/core/registry";
import { loadJS, loadCSS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { CharField } from "@web/views/fields/char/char_field";
import { qweb } from 'web.core';
const { Component, onWillUnmount, onWillUpdateProps, useEffect, useRef, useState, onMounted } = owl;


export class KsMapPreview extends Component {
    setup() {
        var self =this;
        this.root =null;
        this.orm = useService("orm");
        this.mapContainerRef = useRef("mapContainer");
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

    _Ks_render() {
        var self = this;
        var rec = this.props.record.data;
        if ($(self.mapContainerRef.el.parentElement).find("div.text").length){
            $(self.mapContainerRef.el.parentElement).find("div.text").remove();
        }
        if (rec.ks_dashboard_item_type === 'ks_map_view'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Select Group By to create chart view"));
                    } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Select Measure and Group By to create chart view"));
                        var h2Element = document.getElementById("text");
                        h2Element.textContent = " ";
                        var $ChartElement = $(document.getElementById("map_chart"));
                        $ChartElement.hide();
                    } else if (!rec.ks_chart_data_count_type) {
                        $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Select Chart Data Count Type"));
                    } else {
                         var $ChartElement = $(document.getElementById("map_chart"));
                        $ChartElement.show();
                        this.get_map_data(rec);
                    }
                } else {
                    $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Select a Model first."));
                    var $ChartElement = $(document.getElementById("map_chart"));
                        $ChartElement.hide();
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        this.get_map_data(rec);
                } else {
                    $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else {
                    $(self.mapContainerRef.el.parentElement).prepend($("<div class='text'>").text("Please run the appropriate Query"));
                    var h2Element = document.getElementById("text");
                    h2Element.textContent = " ";
            }
        }

    }

    async get_map_data(rec){
        if($(this.mapContainerRef.el).find(".map_text").length){
            $(this.mapContainerRef.el).find(".map_text").remove();
        }
        var ks_data=[];
        let data = [];
        let label_data = [];
        let query_label_data = [];
        let domain = [];
        var partners;
        const chart_data = JSON.parse(this.props.record.data.ks_chart_data);
        if (chart_data.groupByIds){
            domain = [['id', 'in', chart_data.groupByIds]]
            const fields = ["partner_latitude", "partner_longitude", "name"];
            partners = await this.orm.searchRead("res.partner", domain, fields);
        }
        const partners_query = await this._fetchRecordsPartner(rec);

//        const chart_data = JSON.parse(this.props.record.data.ks_chart_data);
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
        if (rec.ks_data_calculation_type === 'query'){
            for (let i=0 ; i<ks_labels.length ; i++){
                if (ks_labels[i] !== false){
                    if (typeof ks_labels[i] == 'string'){
                        if (ks_labels[i].includes(',')){
                            ks_labels[i] = ks_labels[i].split(', ')[1]
                        }
                        query_label_data.push(ks_labels[i])
                    }else{
                        query_label_data.push(ks_labels[i])
                    }
                }
            }
                for (let i=0 ; i<query_label_data.length ; i++){
                    if (typeof query_label_data[i] == 'string'){
                        for (let j=0 ; j<partners_query.length ; j++){
                            if (query_label_data[i] == partners_query[j].name){
                                data.push({"title":query_label_data[i], "latitude":partners_query[j].partner_latitude, "longitude": partners_query[j].partner_longitude});
                            }
                        }
                    }else{
                          data.push({"title":query_label_data[i], "latitude":partners_query[i].partner_latitude, "longitude": partners_query[i].partner_longitude});
                    }
                }
        }
        else if (rec.ks_data_calculation_type !== 'query'){
            for (let i=0 ; i<ks_labels.length ; i++){
                if (ks_labels[i] !== false){
                    if (ks_labels[i].includes(',')){
                        ks_labels[i] = ks_labels[i].split(', ')[1]
                    }
                    label_data.push({'title': ks_labels[i], 'value':ks_data[i]})
                }
            }
            for (let i=0 ; i<label_data.length ; i++){
                for (let j=0 ; j<partners.length ; j++){
                    if (label_data[i].title == partners[j].name){
                        partners[j].name = partners[j].name + ';' + label_data[i].value
                    }
                }
            }
            for (let i=0 ; i<partners.length ; i++){
                data.push({"title":partners[i].name, "latitude":partners[i].partner_latitude, "longitude": partners[i].partner_longitude});
            }
        }

        this.root = am5.Root.new(this.mapContainerRef.el);

        // Set themes
        this.root.setThemes([am5themes_Animated.new(this.root)]);

        // Create the map chart
        var chart = this.root.container.children.push(
          am5map.MapChart.new(this.root, {
            panX: "translateX",
            panY: "translateY",
            projection: am5map.geoMercator()
          })
        );

        var cont = chart.children.push(
          am5.Container.new(this.root, {
            layout: this.root.horizontalLayout,
            x: 20,
            y: 40
          })
        );

        // Add labels and controls
        cont.children.push(
          am5.Label.new(this.root, {
            centerY: am5.p50,
            text: "Map"
          })
        );

        var switchButton = cont.children.push(
          am5.Button.new(this.root, {
            themeTags: ["switch"],
            centerY: am5.p50,
            icon: am5.Circle.new(this.root, {
              themeTags: ["icon"]
            })
          })
        );

        switchButton.on("active", function() {
          if (!switchButton.get("active")) {
            chart.set("projection", am5map.geoMercator());
            chart.set("panY", "translateY");
            chart.set("rotationY", 0);
            backgroundSeries.mapPolygons.template.set("fillOpacity", 0);
          } else {
            chart.set("projection", am5map.geoOrthographic());
            chart.set("panY", "rotateY");

            backgroundSeries.mapPolygons.template.set("fillOpacity", 0.1);
          }
        });

        cont.children.push(
          am5.Label.new(this.root, {
            centerY: am5.p50,
            text: "Globe"
          })
        );

        // Create series for background fill
        var backgroundSeries = chart.series.push(am5map.MapPolygonSeries.new(this.root, {}));
        backgroundSeries.mapPolygons.template.setAll({
          fill: this.root.interfaceColors.get("alternativeBackground"),
          fillOpacity: 0,
          strokeOpacity: 0
        });

//        // Add background polygon
        backgroundSeries.data.push({
          geometry: am5map.getGeoRectangle(90, 180, -90, -180)
        });

        // Create main polygon series for countries
        var polygonSeries = chart.series.push(
          am5map.MapPolygonSeries.new(this.root, {
            geoJSON: am5geodata_worldLow,
            exclude: ["AQ"]
          })
        );
        polygonSeries.mapPolygons.template.setAll({
          tooltipText: "{name}",
          toggleKey: "active",
          interactive: true
        });

        polygonSeries.mapPolygons.template.states.create("hover", {
          fill: this.root.interfaceColors.get("primaryButtonHover")
        });

        polygonSeries.mapPolygons.template.states.create("active", {
          fill: this.root.interfaceColors.get("primaryButtonHover")
        });

        var previousPolygon;

        polygonSeries.mapPolygons.template.on("active", function (active, target) {
          if (previousPolygon && previousPolygon != target) {
            previousPolygon.set("active", false);
          }
          if (target.get("active")) {
            polygonSeries.zoomToDataItem(target.dataItem );
          }
          else {
            chart.goHome();
          }
          previousPolygon = target;
        });

        // Create line series for trajectory lines
        var lineSeries = chart.series.push(am5map.MapLineSeries.new(this.root, {}));
        lineSeries.mapLines.template.setAll({
          stroke: this.root.interfaceColors.get("alternativeBackground"),
          strokeOpacity: 0.3
        });

        // Create point series for markers
        var pointSeries = chart.series.push(am5map.MapPointSeries.new(this.root, {}));
        var colorset = am5.ColorSet.new(this.root, {});
        const self = this;


        pointSeries.bullets.push(function() {
          var container = am5.Container.new(self.root, {
            tooltipText: "{title}",
            cursorOverStyle: "pointer"
          });

          var circle = container.children.push(
            am5.Circle.new(self.root, {
              radius: 4,
              tooltipY: 0,
              fill: colorset.next(),
              strokeOpacity: 0
            })
          );


          var circle2 = container.children.push(
            am5.Circle.new(self.root, {
              radius: 4,
              tooltipY: 0,
              fill: colorset.next(),
              strokeOpacity: 0,
              tooltipText: "{title}"
            })
          );

          circle.animate({
            key: "scale",
            from: 1,
            to: 5,
            duration: 600,
            easing: am5.ease.out(am5.ease.cubic),
            loops: Infinity
          });

          circle.animate({
            key: "opacity",
            from: 1,
            to: 0.1,
            duration: 600,
            easing: am5.ease.out(am5.ease.cubic),
            loops: Infinity
          });

          return am5.Bullet.new(self.root, {
            sprite: container
          });
        });

        for (var i = 0; i < data.length; i++) {
          var final_data = data[i];
          addCity(final_data.longitude, final_data.latitude, final_data.title);
        }
        function addCity(longitude, latitude, title) {
          pointSeries.data.push({
            geometry: { type: "Point", coordinates: [longitude, latitude] },
            title: title,
          });
        }

//        // Add zoom control
        chart.set("zoomControl", am5map.ZoomControl.new(this.root, {}));

        // Set clicking on "water" to zoom out
        chart.chartContainer.get("background").events.on("click", function () {
          chart.goHome();
        })

        // Make stuff animate on load
        chart.appear(1000, 100);

    };

    async _fetchRecordsPartner(data) {
        let domain = [];
        if (data && data['ks_partners_map']) {
            domain = [['id', 'in', JSON.parse(data['ks_partners_map'])]]
        }
        const fields = ["partner_latitude", "partner_longitude", "name"];
        const records = await this.orm.searchRead("res.partner", domain, fields);
        return records
    }

}

KsMapPreview.template = "ks_dashboard_ninja.KsMapPreview";
KsMapPreview.supportedTypes = ["char"];

registry.category("fields").add("ks_dashboard_map_preview", KsMapPreview);