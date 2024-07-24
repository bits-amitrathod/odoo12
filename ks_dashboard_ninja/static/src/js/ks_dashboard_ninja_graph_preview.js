/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import field_utils from 'web.field_utils';
import { loadCSS,loadJS } from "@web/core/assets";
import { qweb } from 'web.core';
import core from 'web.core';
import session from 'web.session';
var KsGlobalFunction = require('ks_dashboard_ninja.KsGlobalFunction');


const { useEffect, useRef, xml, onWillUpdateProps,onMounted,onWillStart} = owl;


 export class KsGraphPreview extends CharField {
ksNumFormatter(num, digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "k"
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "G"
                },
                {
                    value: 1E12,
                    symbol: "T"
                },
                {
                    value: 1E15,
                    symbol: "P"
                },
                {
                    value: 1E18,
                    symbol: "E"
                }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length-1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if (negative) {
                return "-" + (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            } else {
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }
        }
        ksNumIndianFormatter(num, digits) {
            var negative;
            var si = [{
                value: 1,
                symbol: ""
            },
            {
                value: 1E3,
                symbol: "Th"
            },
            {
                value: 1E5,
                symbol: "Lakh"
            },
            {
                value: 1E7,
                symbol: "Cr"
            },
            {
                value: 1E9,
                symbol: "Arab"
            }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if (negative) {
                return "-" + (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            } else {
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }

        }
        ksNumColombianFormatter(num, digits, ks_precision_digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: ""
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "M"
                },
                {
                    value: 1E12,
                    symbol: "M"
                },
                {
                    value: 1E15,
                    symbol: "M"
                },
                {
                    value: 1E18,
                    symbol: "M"
                }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length-1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }

            if (si[i].symbol === 'M'){
//                si[i].value = 1000000;
                num = parseInt(num) / 1000000
                num = field_utils.format.integer(num, Float64Array)
                if (negative) {
                    return "-" + num + si[i].symbol;
                } else {
                    return num + si[i].symbol;
                }
                }else{
                    if (num % 1===0){
                    num = field_utils.format.integer(num, Float64Array)
                    }else{
                        num = field_utils.format.float(num, Float64Array, {digits:[0,ks_precision_digits]});
                    }
                    if (negative) {
                        return "-" + num;
                    } else {
                        return num;
                    }
                }

        }
        _onKsGlobalFormatter(ks_record_count, ks_data_format, ks_precision_digits){
            var self = this;
            if (ks_data_format == 'exact'){
//                return ks_record_count;
                return field_utils.format.float(ks_record_count, Float64Array, {digits: [0, ks_precision_digits]});
            }else{
                if (ks_data_format == 'indian'){
                    return self.ksNumIndianFormatter( ks_record_count, 1);
                }else if (ks_data_format == 'colombian'){
                    return self.ksNumColombianFormatter( ks_record_count, 1, ks_precision_digits);
                }else{
                    return self.ksNumFormatter(ks_record_count, 1);
                }
            }
        }
        ks_monetary(value, currency_id) {
            var currency = session.get_currency(currency_id);
            if (!currency) {
                return value;
            }
            if (currency.position === "after") {
                return value += ' ' + currency.symbol;
            } else {
                return currency.symbol + ' ' + value;
            }
        }
    setup() {
        super.setup();
        const self = this;
         loadJS('/ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js');
         loadJS('/ks_dashboard_ninja/static/lib/js/chartjs-plugin-datalabels.js');
         loadCSS('/ks_dashboard_ninja/static/lib/css/Chart.min.css') ;

        const inputRef = useRef("input");
//        onMounted(this.onMounted);
        useEffect(
            (input) => {
                if (input) {
                    self._Ks_render();
//                    Chart.plugins.unregister(ChartDataLabels)
                }
            },
            () => [inputRef.el]

        );
//        this.ks_set_default_chart_view();
        onWillUpdateProps(this.onWillUpdateProps);


    }


    onWillUpdateProps(){
    this._Ks_render()
}

//    ks_set_default_chart_view() {
//            Chart.plugins.register({
//                afterDraw: function(chart) {
//                    if (chart.data.labels.length === 0) {
//                        // No data is present
//                        var ctx = chart.chart.ctx;
//                        var width = chart.chart.width;
//                        var height = chart.chart.height
//                        chart.clear();
//
//                        ctx.save();
//                        ctx.textAlign = 'center';
//                        ctx.textBaseline = 'middle';
//                        ctx.font = "3rem 'Lucida Grande'";
//                        ctx.fillText('No data available', width / 2, height / 2);
//                        ctx.restore();
//                    }
//                }
//            });
//
//            Chart.Legend.prototype.afterFit = function() {
//                var chart_type = this.chart.config.type;
//                if (chart_type === "pie" || chart_type === "doughnut") {
//                    this.height = this.height;
//                } else {
//                    this.height = this.height + 20;
//                };
//            }
//        }


    _Ks_render() {
    var self=this;

        $(this.input.el.parentElement).find('div').remove()
        $(this.input.el.parentElement).find('input').addClass('d-none')
        var rec = this.props.record.data;
        if (rec.ks_dashboard_item_type !== 'ks_tile' && rec.ks_dashboard_item_type !== 'ks_kpi' && rec.ks_dashboard_item_type !== 'ks_list_view' && rec.ks_dashboard_item_type !== 'ks_to_do') {
            if (rec.ks_model_id) {
                if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                    return  $(self.input.el.parentElement).append($('<div>').text("Select Group by date to create chart based on date groupby"));
                } else if (rec.ks_dashboard_item_type !== 'ks_scatter_chart' && rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                    $(self.input.el.parentElement).append($('<div>').text("Select Group By to create chart view"));
                } else if (rec.ks_dashboard_item_type !== 'ks_scatter_chart' && rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                    $(self.input.el.parentElement).append($('<div>').text("Select Measure and Group By to create chart view"));
                } else if (rec.ks_dashboard_item_type !== 'ks_scatter_chart' && !rec.ks_chart_data_count_type) {
                    $(self.input.el.parentElement).append($('<div>').text("Select Chart Data Count Type"));
                }
                else if(rec.ks_dashboard_item_type === "ks_scatter_chart"){
                        if(rec.ks_scatter_measure_x_id && rec.ks_scatter_measure_y_id ){
                            this._getChartData();
                        }else{
                            $(self.input.el.parentElement).append($('<div>').text("Please Choose Model ,Measure-X , Measure-Y"));
                        }
                }
                else {
                    this._getChartData();
                }
            } else {
                $(self.input.el.parentElement).append($('<div>').text("Select a Model first."));
            }

        }

    }

    _getChartData() {
        var self = this;
        self.shouldRenderChart = true;
        var field = this.props.record.data;
        var ks_chart_name;
        if (field.name) ks_chart_name = field.name;
        else if (field.ks_model_name) ks_chart_name = field.ks_model_id[1];
        else ks_chart_name = "Name";

        this.chart_type = field.ks_dashboard_item_type.split('_')[1];
        this.chart_data = JSON.parse(field.ks_chart_data);

        if (field.ks_chart_cumulative_field){

            for (var i=0; i< this.chart_data.datasets.length; i++){
                var ks_temp_com = 0
                var datasets = {}
                var data = []
                if (this.chart_data.datasets[i].ks_chart_cumulative_field){
                    for (var j=0; j < this.chart_data.datasets[i].data.length; j++)
                        {
                            ks_temp_com = ks_temp_com + this.chart_data.datasets[i].data[j];
                            data.push(ks_temp_com);
                        }
                        datasets.label =  'Cumulative' + this.chart_data.datasets[i].label;
                        datasets.data = data;
                         if (field.ks_chart_cumulative){
                            datasets.type =  'line';
                        }
                        this.chart_data.datasets.push(datasets);
                }
            }
        }
          if (field.ks_as_of_now){
                   for (var i=0; i< this.chart_data.datasets.length; i++){
                       if (this.chart_data.datasets[i].ks_as_of_now){
                            var ks_temp_com = 0
                            var data = []
                            var datasets = {}
                            for (var j=0; j < this.chart_data.datasets[i].data.length; j++)
                                {
                                    ks_temp_com = ks_temp_com + this.chart_data.datasets[i].data[j];
                                    data.push(ks_temp_com);
                                }
                                this.chart_data.datasets[i].data = data.slice(-field.ks_record_data_limit)
                        }else{
                            this.chart_data.datasets[i].data = this.chart_data.datasets[i].data.slice(-field.ks_record_data_limit)
                        }
                   }
                   this.chart_data['labels'] = this.chart_data['labels'].slice(-field.ks_record_data_limit)

            }
        if (field.ks_chart_is_cumulative && field.ks_chart_data_count_type == 'count' && field.ks_dashboard_item_type === 'ks_bar_chart'){


                var ks_temp_com = 0
                var data = []
                var datasets = {}

                    for (var j=0; j < this.chart_data.datasets[0].data.length; j++)
                        {
                            ks_temp_com = ks_temp_com + this.chart_data.datasets[0].data[j];
                            data.push(ks_temp_com);
                        }
                        datasets.label =  'Cumulative' + this.chart_data.datasets[0].label;
                        datasets.data = data;
                        if (field.ks_chart_cumulative){
                            datasets.type =  'line';
                        }
                        this.chart_data.datasets.push(datasets);


        }

        var $chartContainer = $(qweb.render('ks_chart_form_view_container', {
            ks_chart_name: ks_chart_name

        }));
        $(this.input.el.parentElement).append($chartContainer);

        switch (this.chart_type) {
            case "pie":
            case "doughnut":
            case "polarArea":
            case "radar":
                this.chart_family = "circle";
                break;
            case "bar":
            case "horizontalBar":
            case "line":
            case "area":
                this.chart_family = "square"
                break;
            case "scatter":
                this.chart_family = "square"
                break;
            default:
                this.chart_family = "none";
                break;
        }

        if (this.chart_family === "circle") {
            if (this.chart_data && this.chart_data['labels'].length > 30) {
                $(this.input.el.parentElement).find(".card-body").empty().append($("<div style='font-size:20px;'>Too many records for selected Chart Type. Consider using <strong>Domain</strong> to filter records or <strong>Record Limit</strong> to limit the no of records under <strong>30.</strong>"));
                return;
            }
        }
        if ($(this.input.el.parentElement).find('#ksMyChart').length > 0) {
            this.renderChart();
        }
    }


       renderChart() {
        var self = this;
        var rec=this.props.record.data;
        if (rec.ks_chart_measure_field_2.count && rec.ks_dashboard_item_type === 'ks_bar_chart') {
            var self = this;
            var scales = {}
            scales.yAxes = [{
                    type: "linear",
                    display: true,
                    position: "left",
                    id: "y-axis-0",
                    gridLines: {
                        display: true
                    },
                    labels: {
                        show: true,
                    }
                },
                {
                    type: "linear",
                    display: true,
                    position: "right",
                    id: "y-axis-1",
                    labels: {
                        show: true,
                    },
                    ticks: {
                        beginAtZero: true,
                        callback: function(value, index, values) {
                            var ks_selection = self.chart_data.ks_selection;
                            if (ks_selection === 'monetary') {
                                var ks_currency_id = self.chart_data.ks_currency;
                                var ks_data = self._onKsGlobalFormatter(value, rec.ks_data_format, rec.ks_precision_digits);
                                    ks_data = self.ks_monetary(ks_data, ks_currency_id);
                                return ks_data;
                            } else if (ks_selection === 'custom') {
                                var ks_field = self.chart_data.ks_field;
                                return self._onKsGlobalFormatter(value, rec.ks_data_format, rec.ks_precision_digits) + ' ' + ks_field;
                            }else {
                                return self._onKsGlobalFormatter(value, rec.ks_data_format, rec.ks_precision_digits);
                            }
                        },
                    }
                }
            ]

        }
        var chart_plugin = [];
        if (this.props.record.data.ks_show_data_value) {
            chart_plugin.push(ChartDataLabels);
        }
        if (this.props.record.data.ks_dashboard_item_type =="ks_scatter_chart"){
        var scatter_data = []
        for (let i = 0 ; i<this.chart_data['labels'].length ; i++){
            scatter_data.push({"label":this.chart_data['labels'][i],"data":[{'x':this.chart_data['labels'][i],'y':this.chart_data.datasets[0].data[i]}]})
            }
        Object.assign(this.chart_data.datasets,scatter_data)
        }

        this.ksMyChart = new Chart($(this.input.el.parentElement).find('#ksMyChart')[0], {
            type: this.chart_type === "area" ? "line" : this.chart_type,
            plugins: chart_plugin,
            data: {
                labels: this.chart_data['labels'],
                datasets: this.chart_data.datasets,
            },
            options: {
                maintainAspectRatio: false,
                animation: {
                    easing: 'easeInQuad',
                },
                legend: {
                        display: this.props.record.data.ks_hide_legend
                    },
                layout: {
                    padding: {
                        bottom: 0,
                    }
                },
                scales: scales,
                plugins: {
                    datalabels: {
                        backgroundColor: function(context) {
                            return context.dataset.backgroundColor;
                        },
                        borderRadius: 4,
                        color: 'white',
                        font: {
                            weight: 'bold'
                        },
                        anchor: 'center',
                        textAlign: 'center',
                        display: 'auto',
                        clamp: true,
                        formatter: function(value, ctx) {
                            let sum = 0;
                            let dataArr = ctx.dataset.data;
                            dataArr.map(data => {
                                sum += data;
                            });
                            let percentage = sum === 0 ? 0 + "%" : (value * 100 / sum).toFixed(2) + "%";
                            if(self.props.record.data.ks_data_label_type == 'value'){

                                    percentage = value;
                                    var ks_self = self;
                                    var ks_selection = self.chart_data.ks_selection;
                                    if (ks_selection === 'monetary') {
                                        var ks_currency_id = self.chart_data.ks_currency;
                                        var ks_data = KsGlobalFunction._onKsGlobalFormatter(value, rec.ks_data_format, rec.ks_precision_digits);
                                        ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                                        percentage =  ks_data;
                                    } else if (ks_selection === 'custom') {
                                        var ks_field = self.chart_data.ks_field;
                                        percentage =  KsGlobalFunction._onKsGlobalFormatter(value, rec.ks_data_format, rec.ks_precision_digits) + ' ' + ks_field;
                                    }else {
                                        percentage =  KsGlobalFunction._onKsGlobalFormatter(value, rec.ks_data_format, rec.ks_precision_digits);
                                    }

                            }
                            return percentage;
                        },
                    },
                },

            }
        });
        if (this.chart_data && this.chart_data["datasets"].length > 0) {
            self.ksChartColors(rec.ks_chart_item_color, this.ksMyChart, this.chart_type, this.chart_family, rec.ks_show_data_value);

        }
    }

    ksHideFunction (options, recordData, ksChartFamily, chartType) {
        return options;
    }

    ks_chart_color_pallet(gradient, setsCount, palette){
        var chartColors = [];
        var color_set = ['#F04F65', '#f69032', '#fdc233', '#53cfce', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7'];
        if (palette !== "default") {
            //Get a sorted array of the gradient keys
            var gradientKeys = Object.keys(gradient);
            gradientKeys.sort(function(a, b) {
                return +a - +b;
            });
            for (var i = 0; i < setsCount; i++) {
                var gradientIndex = (i + 1) * (100 / (setsCount + 1)); //Find where to get a color from the gradient
                for (var j = 0; j < gradientKeys.length; j++) {
                    var gradientKey = gradientKeys[j];
                    if (gradientIndex === +gradientKey) { //Exact match with a gradient key - just get that color
                        chartColors[i] = 'rgba(' + gradient[gradientKey].toString() + ')';
                        break;
                    } else if (gradientIndex < +gradientKey) { //It's somewhere between this gradient key and the previous
                        var prevKey = gradientKeys[j - 1];
                        var gradientPartIndex = (gradientIndex - prevKey) / (gradientKey - prevKey); //Calculate where
                        var color = [];
                        for (var k = 0; k < 4; k++) { //Loop through Red, Green, Blue and Alpha and calculate the correct color and opacity
                            color[k] = gradient[prevKey][k] - ((gradient[prevKey][k] - gradient[gradientKey][k]) * gradientPartIndex);
                            if (k < 3) color[k] = Math.round(color[k]);
                        }
                        chartColors[i] = 'rgba(' + color.toString() + ')';
                        break;
                    }
                }
            }
        } else {
            for (var i = 0, counter = 0; i < setsCount; i++, counter++) {
                if (counter >= color_set.length) counter = 0; // reset back to the beginning

                chartColors.push(color_set[counter]);
            }

        }
        return chartColors;
    }

    ksChartColors(palette, ksMyChart, ksChartType, ksChartFamily, ks_show_data_value) {
        var self = this;
        var rec=this.props.record.data;
        var currentPalette = "cool";
        if (!palette) palette = currentPalette;
        currentPalette = palette;

        /*Gradients
          The keys are percentage and the values are the color in a rgba format.
          You can have as many "color stops" (%) as you like.
          0% and 100% is not optional.*/
        var gradient;
        switch (palette) {
            case 'cool':
                gradient = {
                    0: [255, 255, 255, 1],
                    20: [220, 237, 200, 1],
                    45: [66, 179, 213, 1],
                    65: [26, 39, 62, 1],
                    100: [0, 0, 0, 1]
                };
                break;
            case 'warm':
                gradient = {
                    0: [255, 255, 255, 1],
                    20: [254, 235, 101, 1],
                    45: [228, 82, 27, 1],
                    65: [77, 52, 47, 1],
                    100: [0, 0, 0, 1]
                };
                break;
            case 'neon':
                gradient = {
                    0: [255, 255, 255, 1],
                    20: [255, 236, 179, 1],
                    45: [232, 82, 133, 1],
                    65: [106, 27, 154, 1],
                    100: [0, 0, 0, 1]
                };
                break;

            case 'default':
                var color_set = ['#F04F65', '#f69032', '#fdc233', '#53cfce', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7']
        }



        //Find datasets and length
        var chartType = ksMyChart.config.type;

        switch (chartType) {
            case "pie":
            case "doughnut":
            case "polarArea":
            case "radar":
                var datasets = ksMyChart.config.data.datasets[0];
                var setsCount = datasets.data.length;
                break;
            case "bar":
            case "horizontalBar":
            case "line":
            case "scatter":
                var datasets = ksMyChart.config.data.datasets;
                var setsCount = datasets.length;
                break;
        }

        //Calculate colors
        var chartColors = this.ks_chart_color_pallet(gradient, setsCount, palette);
        var datasets = ksMyChart.config.data.datasets;
        var options = ksMyChart.config.options;

        options.legend.labels.usePointStyle = true;
        if (ksChartFamily == "circle") {
            if (ks_show_data_value) {
                options.legend.position = 'top';
                options.layout.padding.top = 10;
                options.layout.padding.bottom = 20;
            } else {
                options.legend.position = 'bottom';
            }

            options = this.ksHideFunction(options, this.props.record.data, ksChartFamily, chartType);
            options.plugins.datalabels.align = 'center';
            options.plugins.datalabels.anchor = 'end';
            options.plugins.datalabels.borderColor = 'white';
            options.plugins.datalabels.borderRadius = 25;
            options.plugins.datalabels.borderWidth = 2;
            options.plugins.datalabels.clamp = true;
            options.plugins.datalabels.clip = false;
            options.tooltips.callbacks = {
                title: function(tooltipItem, data) {
                    var ks_self = self;
                    var k_amount = data.datasets[tooltipItem[0].datasetIndex]['data'][tooltipItem[0].index];
                    var ks_selection = ks_self.chart_data.ks_selection;
                    if (ks_selection === 'monetary') {
                        var ks_currency_id = ks_self.chart_data.ks_currency;
                        k_amount = self.ks_monetary(k_amount, ks_currency_id);
                        return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount
                    } else if (ks_selection === 'custom') {
                        var ks_field = ks_self.chart_data.ks_field;
                        //                                                        ks_type = field_utils.format.char(ks_field);
                        k_amount = field_utils.format.float(k_amount, Float64Array, {digits: [0, self.props.record.data.ks_precision_digits]});
                        return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount + " " + ks_field;
                    } else {
                        k_amount = field_utils.format.float(k_amount, Float64Array, {digits: [0, self.props.record.data.ks_precision_digits]});
                        return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount
                    }
                },
                label: function(tooltipItem, data) {
                    return data.labels[tooltipItem.index];
                },

            }
            for (var i = 0; i < datasets.length; i++) {
                if (chartType === "radar"){
                    datasets[i].borderColor = chartColors[i];
                    datasets[i]['datalabels'] = {
                        backgroundColor: chartColors,
                    }
                } else {
                    datasets[i].backgroundColor = chartColors;
                    datasets[i].borderColor = "rgba(255,255,255,1)";
                }

                switch (ksChartType) {
                   case "radar":
                       datasets[i].borderColor = chartColors[i];
                       break;
                }
            }
            if (this.props.record.data.ks_semi_circle_chart && (chartType === "pie" || chartType === "doughnut")) {
                options.rotation = 1 * Math.PI;
                options.circumference = 1 * Math.PI;
            }
        } else if (ksChartFamily == "square") {
            options = this.ksHideFunction(options, this.props.record.data, ksChartFamily, chartType);

            options.scales.xAxes[0].gridLines.display = false;
            options.scales.yAxes[0].ticks.beginAtZero = true;
            options.plugins.datalabels.align = 'end';
            options.plugins.datalabels.formatter = function(value, ctx) {
                var ks_self = self;
                if(self.props.record.data.ks_dashboard_item_type != "ks_scatter_chart"){
                var ks_selection = self.chart_data.ks_selection;
                if (ks_selection === 'monetary') {
                    var ks_currency_id = self.chart_data.ks_currency;
                    var ks_data = self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits);
                        ks_data = self.ks_monetary(ks_data, ks_currency_id);
                    return ks_data;
                } else if (ks_selection === 'custom') {
                    var ks_field = self.chart_data.ks_field;
                    return self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format,self.props.record.data.ks_precision_digits) + ' ' + ks_field;
                }else {
                    return self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits);
                }
                }
                else{
                    return null
                }

            };

            if (chartType === "line") {
                options.plugins.datalabels.backgroundColor = function(context) {
                    return context.dataset.borderColor;
                };
            }


            if (chartType === "horizontalBar") {
                options.scales.xAxes[0].ticks.callback = function(value, index, values) {
                    var ks_self = self;
                    var ks_selection = self.chart_data.ks_selection;
                    if (ks_selection === 'monetary') {
                        var ks_currency_id = self.chart_data.ks_currency;
                        var ks_data = self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits);
                            ks_data = self.ks_monetary(ks_data, ks_currency_id);
                        return ks_data;
                    } else if (ks_selection === 'custom') {
                        var ks_field = self.chart_data.ks_field;
                        return self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits) + ' ' + ks_field;
                    }else {
                        return self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits);
                    }
                }
                options.scales.xAxes[0].ticks.beginAtZero = true;
            } else {
                options.scales.yAxes[0].ticks.callback = function(value, index, values) {
                    var ks_self = self;
                    var ks_selection = ks_self.chart_data.ks_selection;
                    var ks_selection = self.chart_data.ks_selection;
                    if (ks_selection === 'monetary') {
                        var ks_currency_id = self.chart_data.ks_currency;
                        var ks_data = self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits);
                            ks_data = self.ks_monetary(ks_data, ks_currency_id);
                        return ks_data;
                    } else if (ks_selection === 'custom') {
                        var ks_field = self.chart_data.ks_field;
                        return self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits) + ' ' + ks_field;
                    }else {
                        return self._onKsGlobalFormatter(value, self.props.record.data.ks_data_format, self.props.record.data.ks_precision_digits);
                    }
                }
            }
            if (chartType !== 'scatter'){
                options.tooltips.callbacks = {
                    label: function(tooltipItem, data) {
                        var ks_self = self;
                        var k_amount = data.datasets[tooltipItem.datasetIndex]['data'][tooltipItem.index];
                        var ks_selection = ks_self.chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = ks_self.chart_data.ks_currency;
                            k_amount = self.ks_monetary(k_amount, ks_currency_id);
                            return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount
                        } else if (ks_selection === 'custom') {
                            var ks_field = ks_self.chart_data.ks_field;
                            // ks_type = field_utils.format.char(ks_field);
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits: [0, self.props.record.data.ks_precision_digits]});
                            return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount + " " + ks_field;
                        } else {
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,self.props.record.data.ks_precision_digits]});
                            return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount
                        }
                    }
                }
             }

            for (var i = 0; i < datasets.length; i++) {
                switch (ksChartType) {
                    case "bar":
                    case "horizontalBar":
                        if (datasets[i].type && datasets[i].type == "line") {
                            datasets[i].borderColor = chartColors[i];
                            datasets[i].backgroundColor = "rgba(255,255,255,0)";
                            datasets[i]['datalabels'] = {
                                backgroundColor: chartColors[i],
                            }

                        } else {
                            datasets[i].backgroundColor = chartColors[i];
                            datasets[i].borderColor = "rgba(255,255,255,0)";
                            options.scales.xAxes[0].stacked = this.props.record.data.ks_bar_chart_stacked;
                            options.scales.yAxes[0].stacked = this.props.record.data.ks_bar_chart_stacked;
                        }
                        break;
                    case "scatter":
                         datasets[i].backgroundColor = chartColors[i];
                         datasets[i]['datalabels'] = {
                                backgroundColor: chartColors[i],
                         }
                         break;
                    case "line":
                        datasets[i].borderColor = chartColors[i];
                        datasets[i].backgroundColor = "rgba(255,255,255,0)";
                        break;
                    case "area":
                        datasets[i].borderColor = chartColors[i];
                        break;
                }

            }

        }

        ksMyChart.update();
        if ( $(self.input.el.parentElement).find('canvas').height() < 250) {
             $(self.input.el.parentElement).find('canvas').height(250);
        }

    }

}

registry.category("fields").add("ks_dashboard_graph_preview", KsGraphPreview);
return {
        KsGraphPreview: KsGraphPreview,
    }


