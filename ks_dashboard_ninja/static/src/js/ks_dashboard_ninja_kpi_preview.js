/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import field_utils from 'web.field_utils';
import { qweb } from 'web.core';
import utils from 'web.utils';
import session from 'web.session';
var KsGlobalFunction = require('ks_dashboard_ninja.KsGlobalFunction');


const { useEffect, useRef, xml, onWillUpdateProps} = owl;


class KsKpiPreviewowl extends CharField {
file_type_magic_word ={
            '/': 'jpg',
            'R': 'gif',
            'i': 'png',
            'P': 'svg+xml',
        }
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
                        num = field_utils.format.float(num, Float64Array, {digits: [0,ks_precision_digits]});
                    }
                    if (negative) {
                        return "-" + num;
                    } else {
                        return num;
                    }
                }

        }
        ks_get_gcd(a, b) {
            return (b == 0) ? a : this.ks_get_gcd(b, a % b);
        }

        _get_rgba_format(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
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
    setup() {
        super.setup();
        const self = this;
        const inputRef = useRef("input");
        useEffect(
            (input) => {
                if (input) {
                    self.kpi_render();
                }
            },
            () => [inputRef.el]

        );
        onWillUpdateProps(this.onWillUpdateProps);

    }
    onWillUpdateProps(){
        this.kpi_render()
    }

        kpi_render() {
        const self = this;
        var rec = self.props.record.data;
        $(this.input.el.parentElement).find('div').remove()
        $(this.input.el.parentElement).find('input').addClass('d-none')
            if (rec.ks_model_id && rec.ks_dashboard_item_type === "ks_kpi") {
                if (!rec.ks_model_id_2) {
                    if (!(rec.ks_record_count_type === 'count')) {
                        if (rec.ks_record_field) {
                            this.renderKpi();
                        } else {
                             $(self.input.el.parentElement).append($('<div>').text("Select a Record field "))
                        }
                    } else {
                        this.renderKpi();
                    }
                } else {
                    if (!(rec.ks_record_count_type_2 === 'count') && !(rec.ks_record_count_type === 'count')) {
                        if (rec.ks_record_field_2 && rec.ks_record_field) {
                            this.renderKpi();
                        } else {
                           $(self.input.el.parentElement).append($('<div>').text("Select a Record fields "))
                        }
                    } else if (!(rec.ks_record_count_type_2 === 'count') && (rec.ks_record_count_type === 'count')) {
                        if (rec.ks_record_field_2) {
                            this.renderKpi();
                        } else {
                            $(self.input.el.parentElement).append($('<div>').text("Select a Record field"))
                        }
                    } else if ((rec.ks_record_count_type_2 === 'count') && !(rec.ks_record_count_type === 'count')) {
                        if (rec.ks_record_field) {
                            this.renderKpi();
                        } else {
                            $(self.input.el.parentElement).append($('<div>').text("Select a Record field"))
                        }
                    } else {
                        this.renderKpi();
                    }
                }
            } else {
                $(self.input.el.parentElement).append($('<div>').text("Select a Model first"))
            }
        }
        ksSum(count_1, count_2, item_info, field, target_1, $kpi_preview, kpi_data) {
            var self = this;
            var count = count_1 + count_2
            if (field.ks_multiplier_active){
                item_info['count'] = self._onKsGlobalFormatter(count* field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                item_info['count_tooltip'] = field_utils.format.float(count * field.ks_multiplier, Float64Array, {digits: [0, field.ks_precision_digits]});
            }else{

                item_info['count'] = self._onKsGlobalFormatter(count, field.ks_data_format, field.ks_precision_digits, field.ks_precision_digits);
                item_info['count_tooltip'] = field_utils.format.float(count, Float64Array, {digits: [0, field.ks_precision_digits]});
            }
            if (field.ks_multiplier_active){
                count = count * field.ks_multiplier;
            }
            item_info['target_enable'] = field.ks_goal_enable;
            var ks_color = (target_1 - count) > 0 ? "red" : "green";
            item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
            item_info['ks_comparison'] = true;
            var target_deviation = (target_1 - count) > 0 ? Math.round(((target_1 - count) / target_1) * 100) : Math.round((Math.abs((target_1 - count)) / target_1) * 100);
            if (target_deviation !== Infinity) item_info.target_deviation = field_utils.format.integer(target_deviation) + "%";
            else {
                item_info.pre_arrow = false;
                item_info.target_deviation = target_deviation;
            }
            var target_progress_deviation = target_1 == 0 ? 0 : Math.round((count / target_1) * 100);
            item_info.target_progress_deviation = field_utils.format.integer(target_progress_deviation) + "%";
            $kpi_preview = $(qweb.render("ks_kpi_preview_template_2", item_info));
            $kpi_preview.find('.target_deviation').css({
                "color": ks_color
            });
            if (this.props.record.data.ks_target_view === "Progress Bar") {
                $kpi_preview.find('#ks_progressbar').val(target_progress_deviation)
            }
            return $kpi_preview
        }
        ksPercentage(count_1, count_2, field, item_info, target_1, $kpi_preview) {
            if (field.ks_multiplier_active){
                count_1 = count_1 * field.ks_multiplier;
                count_2 = count_2 * field.ks_multiplier;
            }
            if (field.ks_data_format=='exact'){
              var count = (count_1 / count_2) * 100;
            }
            else{
               var count = parseInt((count_1 / count_2) * 100);
            }

            if (field.ks_multiplier_active){
                count = count * field.ks_multiplier;
            }
            if (!count) count = 0;
             if (field.ks_data_format=='exact'){
                item_info['count'] = count ? parseFloat(count.toFixed(2)) + "%" : "0%";
             }
             else{
                item_info['count'] = count ? field_utils.format.integer(count) + "%" : "0%";

             }
            item_info['count_tooltip'] = count ? count + "%" : "0%";
            item_info.target_progress_deviation = item_info['count']
            target_1 = target_1 > 100 ? 100 : target_1;
            item_info.target = target_1 + "%";
            item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
            var ks_color = (target_1 - count) > 0 ? "red" : "green";
            item_info['target_enable'] = field.ks_goal_enable;
            item_info['ks_comparison'] = false;
            item_info.target_deviation = item_info.target > 100 ? 100 : item_info.target;
            $kpi_preview = $(qweb.render("ks_kpi_preview_template_2", item_info));
            $kpi_preview.find('.target_deviation').css({
                "color": ks_color
            });
            if (this.props.record.data.ks_target_view === "Progress Bar") {
                $kpi_preview.find('#ks_progressbar').val(count)
            }
            return $kpi_preview;
        }
        renderKpi() {
            var self = this;
            var field = self.props.record.data;
            var kpi_data = JSON.parse(field.ks_kpi_data);
//            if (field.ks_multiplier_active){
//                var count_1 = kpi_data[0].record_data * field.ks_multiplier;
//                var count_2 = kpi_data[1] * field.ks_multiplier ? kpi_data[1].record_data : undefined;
//                var target_1 = kpi_data[0].target * field.ks_multiplier;
//            }else{
                var count_1 = kpi_data[0].record_data;
                var count_2 = kpi_data[1] ? kpi_data[1].record_data : undefined;
                var target_1 = kpi_data[0].target;
//            }
            var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
            var target_view = field.ks_target_view,
            pre_view = field.ks_prev_view;
            var ks_rgba_background_color = self._get_rgba_format(field.ks_background_color);
            var ks_rgba_font_color = self._get_rgba_format(field.ks_font_color)

            if (field.ks_goal_enable) {
                var diffrence = 0.0
                if(field.ks_multiplier_active){
                    diffrence = (count_1 * field.ks_multiplier) - target_1
                }else{
                    diffrence = count_1 - target_1
                }
                var acheive = diffrence >= 0 ? true : false;
                diffrence = Math.abs(diffrence);
                var deviation = Math.round((diffrence / target_1) * 100)
                if (deviation !== Infinity) deviation = deviation ? field_utils.format.integer(deviation) + '%' : 0 + '%';
            }
            if (field.ks_previous_period && ks_valid_date_selection.indexOf(field.ks_date_filter_selection) >= 0) {
                var previous_period_data = kpi_data[0].previous_period;
                var pre_diffrence = (count_1 - previous_period_data);
                if (field.ks_multiplier_active){
                    var previous_period_data = kpi_data[0].previous_period * field.ks_multiplier;
                    var pre_diffrence = (count_1 * field.ks_multiplier   - previous_period_data);
                }
                var pre_acheive = pre_diffrence > 0 ? true : false;
                pre_diffrence = Math.abs(pre_diffrence);
                var pre_deviation = previous_period_data ? field_utils.format.integer(parseInt((pre_diffrence / previous_period_data) * 100)) + '%' : "100%"
            }
             var target_progress_deviation = String(Math.round((count_1  / target_1) * 100));
             if(field.ks_multiplier_active){
                var target_progress_deviation = String(Math.round(((count_1 * field.ks_multiplier) / target_1) * 100));
             }
            var ks_rgba_icon_color = self._get_rgba_format(field.ks_default_icon_color)
            var item_info = {
                count_1: self.ksNumFormatter(kpi_data[0]['record_data'], 1),
                count_1_tooltip: kpi_data[0]['record_data'],
                count_2: kpi_data[1] ? String(kpi_data[1]['record_data']) : false,
                name: field.name ? field.name : field.ks_model_id[1],
                target_progress_deviation:target_progress_deviation,
                icon_select: field.ks_icon_select,
                default_icon: field.ks_default_icon,
                icon_color: ks_rgba_icon_color,
                target_deviation: deviation,
                target_arrow: acheive ? 'up' : 'down',
                ks_enable_goal: field.ks_goal_enable,
                ks_previous_period: ks_valid_date_selection.indexOf(field.ks_date_filter_selection) >= 0 ? field.ks_previous_period : false,
                target: self.ksNumFormatter(target_1, 1),
                previous_period_data: previous_period_data,
                pre_deviation: pre_deviation,
                pre_arrow: pre_acheive ? 'up' : 'down',
                target_view: field.ks_target_view,
            }

            if (item_info.target_deviation === Infinity) item_info.target_arrow = false;
            item_info.target_progress_deviation = parseInt(item_info.target_progress_deviation) ? field_utils.format.integer(parseInt(item_info.target_progress_deviation)) : "0"
            if (field.ks_icon) {
                if (!utils.is_bin_size(field.ks_icon)) {
                    // Use magic-word technique for detecting image type
                    item_info['img_src'] = 'data:image/' + (self.file_type_magic_word[field.ks_icon[0]] || 'png') + ';base64,' + field.ks_icon;
                } else {
                    item_info['img_src'] = session.url('/web/image', {
                        model: self.env.model.root.resModel,
                        id: JSON.stringify(this.props.record.data.id),
                        field: "ks_icon",
                        // unique forces a reload of the image when the record has been updated
                        unique: String(this.props.record.data.__last_update.ts),
                    });
                }
            }
            if (field.ks_multiplier_active){
                item_info['count_1'] = self._onKsGlobalFormatter(kpi_data[0]['record_data'] * field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                item_info['count_1_tooltip'] = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
                item_info['count_1'] = self._onKsGlobalFormatter(kpi_data[0]['record_data'], field.ks_data_format, field.ks_precision_digits);
            }
            item_info['target'] = self._onKsGlobalFormatter(kpi_data[0].target, field.ks_data_format, field.ks_precision_digits);

            if (field.ks_unit){
            if (field.ks_multiplier_active){
            var ks_record_count = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
            var ks_record_count = kpi_data[0]['record_data']
            }
            var ks_selection = field.ks_unit_selection;
            if (ks_selection === 'monetary') {
            var ks_currency_id = field.ks_currency_id[0];
            var ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
            item_info['count_1'] = ks_data;
            } else if (ks_selection === 'custom') {
            var ks_field = field.ks_chart_unit;
            item_info['count_1']=ks_field+" "+KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
            }else {
            item_info['count_1']= KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
            }
            }


            var $kpi_preview;
            if (!kpi_data[1]) {
                if (target_view === "Number" || !field.ks_goal_enable) {
                    $kpi_preview = $(qweb.render("ks_kpi_preview_template", item_info));
                } else if (target_view === "Progress Bar" && field.ks_goal_enable) {
                    $kpi_preview = $(qweb.render("ks_kpi_preview_template_3", item_info));
                    $kpi_preview.find('#ks_progressbar').val(parseInt(item_info.target_progress_deviation));
                }

                if (field.ks_goal_enable) {
                    if (acheive) {
                        $kpi_preview.find(".target_deviation").css({
                            "color": "green",
                        });
                    } else {
                        $kpi_preview.find(".target_deviation").css({
                            "color": "red",
                        });
                    }
                }
                if (field.ks_previous_period && String(previous_period_data) && ks_valid_date_selection.indexOf(field.ks_date_filter_selection) >= 0) {
                    if (pre_acheive) {
                        $kpi_preview.find(".pre_deviation").css({
                            "color": "green",
                        });
                    } else {
                        $kpi_preview.find(".pre_deviation").css({
                            "color": "red",
                        });
                    }
                }
                if ($kpi_preview.find('.row').children().length !== 2) {
                    $kpi_preview.find('.row').children().addClass('text-center');
                }
            } else {
                switch (field.ks_data_comparison) {
                    case "None":
                         if (field.ks_multiplier_active){
                            var count_tooltip = String(count_1 * field.ks_multiplier) + "/" + String(count_2 * field.ks_multiplier);
                            var count = String(self.ksNumFormatter(count_1 * field.ks_multiplier, 1)) + "/" + String(self.ksNumFormatter(count_2 * field.ks_multiplier, 1));
                            var data1 = KsGlobalFunction._onKsGlobalFormatter(count_1 * field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                            var data2 = KsGlobalFunction._onKsGlobalFormatter(count_2 * field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                            if (field.ks_unit){
                            var ks_selection = field.ks_unit_selection;
                            if (ks_selection === 'monetary') {
                            var ks_currency_id = field.ks_currency_id[0];
                            data1 = KsGlobalFunction.ks_monetary(data1, ks_currency_id);
                            data2 = KsGlobalFunction.ks_monetary(data2, ks_currency_id)
                            item_info['count'] = data1+"/"+data2;
                            } else if (ks_selection === 'custom') {
                            var ks_field = field.ks_chart_unit;
                            data1= ks_field+" "+data1
                            data2= ks_field+" "+data2
                            item_info['count']= data1+"/"+data2
                            }
                            }else {
                            item_info['count']=String(self._onKsGlobalFormatter(count_1, field.ks_data_format, field.ks_precision_digits)) + "/" + String(self._onKsGlobalFormatter(count_2, field.ks_data_format, field.ks_precision_digits));
                            }
                         }else{
                            var count_tooltip = String(count_1) + "/" + String(count_2);
                            var count = String(self.ksNumFormatter(count_1, 1)) + "/" + String(self.ksNumFormatter(count_2, 1));
                           var data1 = KsGlobalFunction._onKsGlobalFormatter(count_1 , field.ks_data_format, field.ks_precision_digits);
                            var data2 = KsGlobalFunction._onKsGlobalFormatter(count_2 , field.ks_data_format, field.ks_precision_digits);
                            if (field.ks_unit){
                            var ks_selection = field.ks_unit_selection;
                            if (ks_selection === 'monetary') {
                            var ks_currency_id = field.ks_currency_id[0];
                            data1 = KsGlobalFunction.ks_monetary(data1, ks_currency_id);
                            data2 = KsGlobalFunction.ks_monetary(data2, ks_currency_id)
                            item_info['count'] = data1+"/"+data2;
                            } else{
                            var ks_field = field.ks_chart_unit;
                            data1= ks_field+" "+data1
                            data2= ks_field+" "+data2
                            item_info['count']= data1+"/"+data2
                            }
                         }else {
                              item_info['count'] = String(self._onKsGlobalFormatter(count_1, field.ks_data_format, field.ks_precision_digits)) + "/" + String(self._onKsGlobalFormatter(count_2, field.ks_data_format, field.ks_precision_digits));

                            }
                        }
                        item_info['count_tooltip'] = count_tooltip
                        item_info['target_enable'] = false;
                        $kpi_preview = $(qweb.render("ks_kpi_preview_template_2", item_info));
                        break;
                    case "Sum":
                        $kpi_preview = self.ksSum(count_1, count_2, item_info, field, target_1, $kpi_preview, kpi_data);
                        break;
                    case "Percentage":
                        $kpi_preview = self.ksPercentage(count_1, count_2, field, item_info, target_1, $kpi_preview);
                        break;
                    case "Ratio":
                        var gcd = self.ks_get_gcd(Math.round(count_1), Math.round(count_2));
                        if (field.ks_data_format == 'exact'){
                            if (count_1 && count_2) {
                            item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                            item_info['count'] = field_utils.format.float(count_1 / gcd, Float64Array,{digits: [0, field.ks_precision_digits]}) + ":" + field_utils.format.float(count_2 / gcd, Float64Array, {digits: [0, field.ks_precision_digits]});
                            } else {
                            item_info['count_tooltip'] = count_1 + ":" + count_2;
                            item_info['count'] = count_1 + ":" + count_2
                                   }
                          }else{
                            if (count_1 && count_2) {
                            item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                            item_info['count'] = self.ksNumFormatter(count_1 / gcd, 1) + ":" + self.ksNumFormatter(count_2 / gcd, 1);
                            }else {
                            item_info['count_tooltip'] = (count_1) + ":" + count_2;
                            item_info['count'] = self.ksNumFormatter(count_1, 1) + ":" + self.ksNumFormatter(count_2, 1);
                                  }
                          }
                        item_info['target_enable'] = false;
                        $kpi_preview = $(qweb.render("ks_kpi_preview_template_2", item_info));
                        break;
                }
            }
//            $kpi_preview.css({
//                "background-color": ks_rgba_background_color,
//                "color": ks_rgba_font_color,
//            });
            this.ks_kpi_preview_background_style($kpi_preview, ks_rgba_background_color, ks_rgba_font_color);
             $(this.input.el.parentElement).append($kpi_preview);
        }

        ks_kpi_preview_background_style($kpi_preview, ks_rgba_background_color, ks_rgba_font_color){
            $kpi_preview.css({
                "background-color": ks_rgba_background_color,
                "color": ks_rgba_font_color,
            });
        }

        ks_get_gcd(a, b) {
            return (b == 0) ? a : this.ks_get_gcd(b, a % b);
        }
        _get_rgba_format(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }

    }

registry.category("fields").add("ks_dashboard_kpi_owlpreview",KsKpiPreviewowl);
return {
        KsKpiPreviewowl: KsKpiPreviewowl,
    }