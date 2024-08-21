odoo.define('ks_dashboard_ninja_ninja.ks_dashboard', function(require) {
    "use strict";

    var core = require('web.core');
    const { patch } = require('web.utils');
    const { WebClient } = require("@web/webclient/webclient");
    var Dialog = require('web.Dialog');
    var viewRegistry = require('web.view_registry');
    var _t = core._t;
    var QWeb = core.qweb;
    var utils = require('web.utils');
    var config = require('web.config');
    var framework = require('web.framework');
    var time = require('web.time');
    var datepicker = require("web.datepicker");

    const session = require('web.session');
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var framework = require('web.framework');
    var field_utils = require('web.field_utils');
    var KsGlobalFunction = require('ks_dashboard_ninja.KsGlobalFunction');

    var KsQuickEditView = require('ks_dashboard_ninja.quick_edit_view');
    const { loadBundle } = require('@web/core/assets');


    var KsAIDashboardNinja = AbstractAction.extend({
        // To show or hide top control panel flag.
        hasControlPanel: false,

        dependencies: ['bus_service'],

        /**
         * @override
         */

        jsLibs: [
            '/ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js',
            '/ks_dashboard_ninja/static/lib/js/gridstack-h5.js',
            '/ks_dashboard_ninja/static/lib/js/chartjs-plugin-datalabels.js',
            '/ks_dashboard_ninja/static/lib/js/pdfmake.min.js',
            '/ks_dashboard_ninja/static/lib/js/vfs_fonts.js',
        ],
        cssLibs: ['/ks_dashboard_ninja/static/lib/css/Chart.css',
            '/ks_dashboard_ninja/static/lib/css/Chart.min.css'
        ],

        init: function(parent, state, params) {
//            css_grid = $('.o_rtl').length>0 ?
            this._super.apply(this, arguments);
            this.reload_menu_option = {
                reload: state.context.ks_reload_menu,
                menu_id: state.context.ks_menu_id
            };
            this.ks_mode = 'active';
            this.ks_ai_dash_id = state.context['ks_dash_id'];
            this.ks_ai_dash_name = state.context['ks_dash_name'];
            this.ks_ai_del_id = state.context['ks_delete_dash_id'];
            this.action_manager = parent;
            this.controllerID = params.controllerID;
            this.name = "ks_dashboard";
            this.ksIsDashboardManager = false;
            this.ksDashboardEditMode = false;
            this.ksNewDashboardName = false;
            this.file_type_magic_word = {
                '/': 'jpg',
                'R': 'gif',
                'i': 'png',
                'P': 'svg+xml',
            };
            this.ksAllowItemClick = true;
            this.ksSelectedgraphid = [];

            //Dn Filters Iitialization
            var l10n = _t.database.parameters;
            this.form_template = 'ks_dashboard_ninja_template_view';
            this.date_format = time.strftime_to_moment_format(_t.database.parameters.date_format)
            this.date_format = this.date_format.replace(/\bYY\b/g, "YYYY");
            this.datetime_format = time.strftime_to_moment_format((_t.database.parameters.date_format + ' ' + l10n.time_format))
            //            this.is_dateFilter_rendered = false;
            this.ks_date_filter_data;

            // Adding date filter selection options in dictionary format : {'id':{'days':1,'text':"Text to show"}}
            this.ks_date_filter_selections = {
                'l_none': _t('Date Filter'),
                'l_day': _t('Today'),
                't_week': _t('This Week'),
                'td_week': _t('Week To Date'),
                't_month': _t('This Month'),
                'td_month': _t('Month to Date'),
                't_quarter': _t('This Quarter'),
                'td_quarter': _t('Quarter to Date'),
                't_year': _t('This Year'),
                'td_year': _t('Year to Date'),
                'n_day': _t('Next Day'),
                'n_week': _t('Next Week'),
                'n_month': _t('Next Month'),
                'n_quarter': _t('Next Quarter'),
                'n_year': _t('Next Year'),
                'ls_day': _t('Last Day'),
                'ls_week': _t('Last Week'),
                'ls_month': _t('Last Month'),
                'ls_quarter': _t('Last Quarter'),
                'ls_year': _t('Last Year'),
                'l_week': _t('Last 7 days'),
                'l_month': _t('Last 30 days'),
                'l_quarter': _t('Last 90 days'),
                'l_year': _t('Last 365 days'),
                'ls_past_until_now': _t('Past Till Now'),
                'ls_pastwithout_now': _t('Past Excluding Today'),
                'n_future_starting_now': _t('Future Starting Now'),
                'n_futurestarting_tomorrow': _t('Future Starting Tomorrow'),
                'l_custom': _t('Custom Filter'),
            };
            // To make sure date filter show date in specific order.
            this.ks_date_filter_selection_order = ['l_day', 't_week', 't_month', 't_quarter','t_year',
                'td_week','td_month','td_quarter', 'td_year','n_day','n_week', 'n_month', 'n_quarter', 'n_year',
                'ls_day','ls_week', 'ls_month', 'ls_quarter', 'ls_year', 'l_week', 'l_month', 'l_quarter', 'l_year',
                'ls_past_until_now', 'ls_pastwithout_now','n_future_starting_now', 'n_futurestarting_tomorrow',
                 'l_custom'
            ];

            this.ks_dashboard_id = state.params.ks_dashboard_id;

            this.gridstack_options = {
                staticGrid:true,
                float: false,
                cellHeight: 80,
                styleInHead : true,
//                disableOneColumnMode: true,

            };
            if (config.device.isMobileDevice) {
                this.gridstack_options.disableOneColumnMode = false
            }
            this.gridstackConfig = {};
            this.grid = false;
            this.chartMeasure = {};
            this.chart_container = {};
            this.list_container = {};


            this.ksChartColorOptions = ['default', 'cool', 'warm', 'neon'];
//            this.ksUpdateDashboardItem = this.ksUpdateDashboardItem.bind(this);


            this.ksDateFilterSelection = false;
            this.ksDateFilterStartDate = false;
            this.ksDateFilterEndDate = false;
            this.ksUpdateDashboard = {};
            $("head").append('<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">');
            if(state.context.ks_reload_menu){
                this.trigger_up('reload_menu_data', { keep_open: true, scroll_to_bottom: true});
            }
            var context = {
                ksDateFilterSelection: self.ksDateFilterSelection,
                ksDateFilterStartDate: self.ksDateFilterStartDate,
                ksDateFilterEndDate: self.ksDateFilterEndDate,
            }
            this.state = {}
            this.state['user_context']=context
        },

        getContext: function() {
            var self = this;
            var context = {
                ksDateFilterSelection: self.ksDateFilterSelection,
                ksDateFilterStartDate: self.ksDateFilterStartDate,
                ksDateFilterEndDate: self.ksDateFilterEndDate,
            }
            if(self.state['user_context']['ksDateFilterSelection'] !== undefined && self.ksDateFilterSelection !== 'l_none'){
                context = self.state['user_context']
            }
            return Object.assign(context, session.user_context);
        },

        on_attach_callback: function() {
            var self = this;
            $.when(self.ks_fetch_items_data()).then(function(result){
                self.ksRenderDashboard();
                self.ks_set_update_interval();
                if (self.ks_dashboard_data.ks_item_data) {
                    session.user_context['gridstack_config'] = self.ks_get_current_gridstack_config();
                }
            });
        },

        ks_set_update_interval: function() {
            var self = this;
            if (self.ks_dashboard_data.ks_item_data) {

                Object.keys(self.ks_dashboard_data.ks_item_data).forEach(function(item_id) {
                    var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                    var updateValue = self.ks_dashboard_data.ks_set_interval;
                    if (updateValue) {
                        if (!(item_id in self.ksUpdateDashboard)) {
                            if (['ks_tile', 'ks_list_view', 'ks_kpi', 'ks_to_do'].indexOf(item_data['ks_dashboard_item_type']) >= 0) {
                                var ksItemUpdateInterval = setInterval(function() {
                                    self.ksFetchUpdateItem(item_id)
                                }, updateValue);
                            } else {
                                var ksItemUpdateInterval = setInterval(function() {
                                    self.ksFetchChartItem(item_id)
                                }, updateValue);
                            }
                            self.ksUpdateDashboard[item_id] = ksItemUpdateInterval;
                        }
                    }
                });
            }
        },



        ks_remove_update_interval: function() {
            var self = this;
            if (self.ksUpdateDashboard) {
                Object.values(self.ksUpdateDashboard).forEach(function(itemInterval) {
                    clearInterval(itemInterval);
                });
                self.ksUpdateDashboard = {};
            }
        },


        events: {
            'click .ks_dashboarditem_chart_container' : 'onkschartcontainerclick',
            'click .ks_list_view_container':'onkschartcontainerclick',
            'click .ks_dashboard_kpi_dashboard':'onkschartcontainerclick',
            'click #ks_ai_add_item' : 'onKsaddItemClick',
            'click #ks_close_dialog' :'onksaideletedash',
            'click #ks_ai_add_all_item' :'onselectallitems',
            'click #ks_ai_remove_all_item' :'onremoveallitems',
            'click .ks_dashboard_menu_container': function(e) {
                e.stopPropagation();
            },
            'click .ks_qe_dropdown_menu': function(e) {
                e.stopPropagation();
            },
        },


        willStart: function() {
            var self = this;
            var def;
            if (this.reload_menu_option.reload && this.reload_menu_option.menu_id) {
                def = this.getParent().actionService.ksDnReloadMenu(this.reload_menu_option.menu_id);
            }
            return $.when(def, loadBundle(this), this._super()).then(function() {
                return self.ks_fetch_data();
            });
        },

        start: function() {
            var self = this;
            self.ks_set_default_chart_view();
            return this._super()
        },

        ks_set_default_chart_view: function() {
            Chart.plugins.unregister(ChartDataLabels);
            var backgroundColor = 'white';
            Chart.plugins.register({
                beforeDraw: function(c) {
                    var ctx = c.chart.ctx;
                    ctx.fillStyle = backgroundColor;
                    ctx.fillRect(0, 0, c.chart.width, c.chart.height);
                }
            });
            Chart.plugins.register({
                afterDraw: function(chart) {
                    if (chart.data.labels.length === 0) {
                        // No data is present
                        var ctx = chart.chart.ctx;
                        var width = chart.chart.width;
                        var height = chart.chart.height
                        chart.clear();

                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.font = "3rem 'Lucida Grande'";
                        ctx.fillText('No data available', width / 2, height / 2);
                        ctx.restore();
                    }
                }

            });

            Chart.Legend.prototype.afterFit = function() {
                var chart_type = this.chart.config.type;
                if (chart_type === "pie" || chart_type === "doughnut") {
                    this.height = this.height;
                } else {
                    this.height = this.height + 20;
                };
            };
        },



        //To fetch dashboard data.
        ks_fetch_data: function() {
            var self = this;
            return this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_dashboard_data',
                args: [self.ks_dashboard_id],
                context: self.getContext(),
            }).then(function(result) {
//                result = self.normalize_dn_data(result);
                self.ks_dashboard_data = result;
                if(self.state['domain_data'] != undefined){
                    self.ks_dashboard_data.ks_dashboard_domain_data=self.state['domain_data']
                    Object.values(self.ks_dashboard_data.ks_dashboard_pre_domain_filter).map((x)=>{
                        if(self.state['domain_data'][x['model']] != undefined){
                            if(self.state['domain_data'][x['model']]['ks_domain_index_data'][0]['label'].indexOf(x['name']) ==-1){
                                self.ks_dashboard_data.ks_dashboard_pre_domain_filter[x['id']].active = false;
                            }
                        }
                        else{
                            self.ks_dashboard_data.ks_dashboard_pre_domain_filter[x['id']].active = false;
                        }
                    })
                }
            });
        },

        normalize_dn_data: function(result){
            _(result.ks_child_boards).each((x,y)=>{if (typeof(y)==='number'){
                result[y.toString()] = result[y];
                delete result[y];
            }})
            return result;
        },

        ks_fetch_items_data: function(){
            var self = this;
            var items_promises = []
            self.ks_dashboard_data.ks_dashboard_items_ids.forEach(function(item_id){
                items_promises.push(self._rpc({
                    model: "ks_dashboard_ninja.board",
                    method: "ks_fetch_item",
                    context: self.getContext(),
                    args : [[item_id], self.ks_dashboard_id, self.ksGetParamsForItemFetch(item_id)]
                }).then(function(result){
                    self.ks_dashboard_data.ks_item_data[item_id] = result[item_id];
                }));
            });

            return Promise.all(items_promises)
        },

        ksGetParamsForItemFetch: function(){
            return {};
        },

        on_reverse_breadcrumb: function(state) {
            var self = this;
            self.trigger_up('push_state', {
                controllerID: this.controllerID,
                state: state || {},
            });
            return $.when(self.ks_fetch_data());
        },


        ks_get_dark_color: function(color, opacity, percent) {
            var num = parseInt(color.slice(1), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
        },


        //    This is to convert color #value into RGB format to add opacity value.
        _ks_get_rgba_format: function(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        },

        ksRenderDashboard: function() {
            var self = this;
            self.$el.empty();
            self.$el.addClass('ks_dashboard_ninja d-flex flex-column');
            var dash_name = $('ul[id="ks_dashboard_layout_dropdown_container"] li[class="ks_dashboard_layout_event ks_layout_selected"] span').text()
            if (self.ks_dashboard_data.ks_child_boards) self.ks_dashboard_data.name = this.ks_dashboard_data.ks_child_boards[self.ks_dashboard_data.ks_selected_board_id][0];
            var $ks_header = $(QWeb.render('ksDashboardNinjaHeader', {
                ks_dashboard_name: self.ks_dashboard_data.name,
                ks_multi_layout: self.ks_dashboard_data.multi_layouts,
                ks_dash_name: self.ks_dashboard_data.name,
                ks_dashboard_manager: false,
                ks_ai_dashboard : true,
                date_selection_data: self.ks_date_filter_selections,
                date_selection_order: self.ks_date_filter_selection_order,
                ks_show_create_layout_option: (Object.keys(self.ks_dashboard_data.ks_item_data).length > 0) && self.ks_dashboard_data.ks_dashboard_manager,
                ks_show_layout: self.ks_dashboard_data.ks_dashboard_manager && self.ks_dashboard_data.ks_child_boards && true,
                ks_selected_board_id: self.ks_dashboard_data.ks_selected_board_id,
                ks_child_boards: self.ks_dashboard_data.ks_child_boards,
                ks_dashboard_data: self.ks_dashboard_data,
                ks_dn_pre_defined_filters: _(self.ks_dashboard_data.ks_dashboard_pre_domain_filter).values().sort(function(a, b){return a.sequence - b.sequence}),
            }));

            if (!config.device.isMobile) {
                $ks_header.addClass("ks_dashboard_header_sticky")
            }

            self.$el.append($ks_header);
            $(document.querySelectorAll(".modal-body .ks_dashboard_header .ks_date_filter_selection_input")).remove()
            $(document.querySelectorAll(".modal-body .ks_dashboard_header .ks_dashboard_ai_dashboard")).remove()
            $(document.querySelectorAll(".modal-body .ks_dashboard_header #ks_dashboard_title")).remove()
            $(document.querySelector(".modal-header .btn-close")).addClass("d-none")
            $(document.querySelector(".modal-header .o_debug_manager")).addClass("d-none")
            if ($(document.querySelector(".modal-body .ks_start_tv_dashboard"))){
                $(document.querySelector(".modal-body .ks_start_tv_dashboard")).remove()
            }
            if ($(document.querySelector(".modal-body .ks_dashboard_print_pdf"))){
                $(document.querySelector(".modal-body .ks_dashboard_print_pdf")).remove()
            }
            if ($(document.querySelector(".modal-body .ks_dashboard_send_email"))){
                 $(document.querySelector(".modal-body .ks_dashboard_send_email")).remove()
            }
            if ($(document.querySelector(".modal-body .ks-dashboard-switch"))){
                 $(document.querySelector(".modal-body .ks-dashboard-switch")).remove()
            }

            if (Object.keys(self.ks_dashboard_data.ks_item_data).length===0){
                self.$el.find('.ks_dashboard_link').addClass("d-none");
                self.$el.find('.ks_dashboard_edit_layout').addClass("d-none");
            }
            self.ksRenderDashboardMainContent();
            if (Object.keys(self.ks_dashboard_data.ks_item_data).length === 0) {
                self._ksRenderNoItemView();
            }


        },

        ksRenderDashboardMainContent: function() {
            var self = this;
            if (config.device.isMobile && $('#ks_dn_layout_button :first-child').length > 0) {
                $('.ks_am_element').append($('#ks_dn_layout_button :first-child')[0].innerText);
                this.$el.find("#ks_dn_layout_button").addClass("ks_hide");
            }
            if (self.ks_dashboard_data.ks_item_data) {
//                self._renderDateFilterDatePicker();

                self.$el.find('.ks_dashboard_link').removeClass("ks_hide");

                $('.ks_dashboard_items_list').remove();
                var $dashboard_body_container = $(QWeb.render('ks_main_body_container'))
                var $gridstackContainer = $dashboard_body_container.find(".grid-stack");
                $dashboard_body_container.appendTo(self.$el)
                self.grid = GridStack.init(self.gridstack_options,$gridstackContainer[0]);
                var items = self.ksSortItems(self.ks_dashboard_data.ks_item_data);

                self.ksRenderDashboardItems(items);

                // In gridstack version 0.3 we have to make static after adding element in dom
                self.grid.setStatic(true);

            } else if (!self.ks_dashboard_data.ks_item_data) {
                self.$el.find('.ks_dashboard_link').addClass("ks_hide");
                self._ksRenderNoItemView();
            }
        },

        // This function is for maintaining the order of items in mobile view
        ksSortItems: function(ks_item_data) {
            var items = []
            var self = this;
            var item_data = Object.assign({}, ks_item_data);
            if (self.ks_dashboard_data.ks_gridstack_config) {
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
                var a = Object.values(self.gridstackConfig);
                var b = Object.keys(self.gridstackConfig);
                for (var i = 0; i < a.length; i++) {
                    a[i]['id'] = b[i];
                }
                a.sort(function(a, b) {
                    return (35 * a.y + a.x) - (35 * b.y + b.x);
                });
                for (var i = 0; i < a.length; i++) {
                    if (item_data[a[i]['id']]) {
                        items.push(item_data[a[i]['id']]);
                        delete item_data[a[i]['id']];
                    }
                }
            }

            return items.concat(Object.values(item_data));
        },

        ksRenderDashboardItems: function(items) {
            var self = this;
            self.$el.find('.print-dashboard-btn').addClass("ks_pro_print_hide");
            if (self.ks_dashboard_data.ks_gridstack_config) {
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
            }
            var item_view;
            var ks_container_class = 'grid-stack-item',
                ks_inner_container_class = 'grid-stack-item-content';
                for (var i = 0; i < items.length; i++) {
                if (self.grid) {
                if (items[i].ks_dashboard_item_type === 'ks_list_view') {
                        self._renderListView(items[i], self.grid)

                }else if(items[i].ks_dashboard_item_type === 'ks_kpi'){
                    var $kpi_preview = self.renderKpi(items[i], self.grid)
                        if (items[i].id in self.gridstackConfig) {
                            if (config.device.isMobile){
                                self.grid.addWidget($kpi_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:true,minW:2,maxW:null,minH:2,maxH:3,id:items[i].id});
                             }
                             else{
                                self.grid.addWidget($kpi_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:false,minW:2,maxW:null,minH:2,maxH:3,id:items[i].id});
                             }
                        } else {
                             self.grid.addWidget($kpi_preview[0], {x:0, y:0, w:3, h:2,autoPosition:true,minW:2,maxW:null,minH:2,maxH:3,id:items[i].id});
                             $(document.querySelector(".modal-body .ks_dashboard_item_button_container")).remove();
                        }
                }else{
                    self._renderGraph(items[i], self.grid)
                }

                }
            }
        },


        ks_container_option: function(chart_title, ksIsDashboardManager, ksIsUser, ks_dashboard_list, chart_id, chart_family, chart_type, ksChartColorOptions, ks_info, ks_company){
            var container_data = {
                ks_chart_title: chart_title,
                ksIsDashboardManager: ksIsDashboardManager,
                ksIsUser:ksIsUser,
                ks_dashboard_list: ks_dashboard_list,
                chart_id: chart_id,
                chart_family: chart_family,
                chart_type: chart_type,
                ksChartColorOptions: ksChartColorOptions,
                ks_info:ks_info,
                ks_company:ks_company
            }
            return container_data;
        },

        ks_set_selected_color_pallet: function($ks_gridstack_container, item){
            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('ks_date_filter_selected');
        },

        _renderGraph: function(item) {
            var self = this;
            var chart_data = JSON.parse(item.ks_chart_data);
            var isDrill = item.isDrill ? item.isDrill : false;
            var chart_id = item.id,
                chart_title = item.name;
            var chart_title = item.name;
            var chart_type = item.ks_dashboard_item_type.split('_')[1];
            switch (chart_type) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    var chart_family = "circle";
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                case "area":
                    var chart_family = "square"
                    break;
                default:
                    var chart_family = "none";
                    break;

            }
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }

            var container_data = this.ks_container_option(chart_title, false, false, self.ks_dashboard_data.ks_dashboard_list, chart_id, chart_family, chart_type, this.ksChartColorOptions, ks_description, item.ks_company);

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_container', container_data)).addClass('ks_dashboarditem_id');

            self.ks_set_selected_color_pallet($ks_gridstack_container, item);
//            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('ks_date_filter_selected');

            var ksLayoutGridId = $(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id')
            if(ksLayoutGridId && ksLayoutGridId != 'ks_default'){
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_child_boards[parseInt(ksLayoutGridId)][1])
            }
            parseInt($(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id'))
            if (chart_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:true,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
                else{
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:false,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
//                self.grid.addWidget($ks_gridstack_container, self.gridstackConfig[chart_id].x, self.gridstackConfig[chart_id].y, self.gridstackConfig[chart_id].width, self.gridstackConfig[chart_id].height, false, 11, null, 3, null, chart_id);
            } else {
//                self.grid.addWidget($ks_gridstack_container, 0, 0, 13, 4, true, 11, null, 3, null, chart_id);
                  self.grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:6, h:4,autoPosition:true,minW:4,maxW:null,minH:3,maxH:null, id :chart_id});
            }
            $(document.querySelector(".modal-body .ks_dashboard_item_button_container")).remove();
            self._renderChart($ks_gridstack_container, item);
        },

        ks_chart_color_pallet: function(gradient, setsCount, palette, item){
            var chartColors = [];
            var color_set = ['#F04F65', '#f69032', '#fdc233', '#53cfce', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7']
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
        },

        _renderChart: function($ks_gridstack_container, item) {
            var self = this;
            var chart_data = JSON.parse(item.ks_chart_data);

            if (item.ks_chart_cumulative_field){

                for (var i=0; i< chart_data.datasets.length; i++){
                    var ks_temp_com = 0
                    var data = []
                    var datasets = {}
                    if (chart_data.datasets[i].ks_chart_cumulative_field){
                        for (var j=0; j < chart_data.datasets[i].data.length; j++)
                            {
                                ks_temp_com = ks_temp_com + chart_data.datasets[i].data[j];
                                data.push(ks_temp_com);
                            }
                            datasets.label =  'Cumulative' + chart_data.datasets[i].label;
                            datasets.data = data;
                            if (item.ks_chart_cumulative){
                                datasets.type =  'line';
                            }
                            chart_data.datasets.push(datasets);
                    }
                }
            }
            if (item.ks_chart_is_cumulative && item.ks_chart_data_count_type == 'count' && item.ks_dashboard_item_type === 'ks_bar_chart'){
                var ks_temp_com = 0
                var data = []
                var datasets = {}
                for (var j=0; j < chart_data.datasets[0].data.length; j++){
                        ks_temp_com = ks_temp_com + chart_data.datasets[0].data[j];
                        data.push(ks_temp_com);
                    }
                datasets.label =  'Cumulative' + chart_data.datasets[0].label;
                datasets.data = data;
                if (item.ks_chart_cumulative){
                    datasets.type =  'line';
                }
                chart_data.datasets.push(datasets);
            }
            var isDrill = item.isDrill ? item.isDrill : false;
            var chart_id = item.id,
                chart_title = item.name;
            var chart_title = item.name;
            var chart_type = item.ks_dashboard_item_type.split('_')[1];
            switch (chart_type) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    var chart_family = "circle";
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                case "area":
                    var chart_family = "square"
                    break;
                default:
                    var chart_family = "none";
                    break;

            }
            $ks_gridstack_container.find('.ks_color_pallate').data({
                chartType: chart_type,
                chartFamily: chart_family
            }); {
                chartType: "pie"
            }
            var $ksChartContainer = $('<canvas id="ks_chart_canvas_id" data-chart-id=' + chart_id + '/>');
            $ks_gridstack_container.find('.card-body').append($ksChartContainer);
            if (!item.ks_show_records) {
                $ks_gridstack_container.find('.ks_dashboard_item_chart_info').hide();
            }
            item.$el = $ks_gridstack_container;
            if (chart_family === "circle") {
                if (chart_data && chart_data['labels'].length > 30) {
                    $ks_gridstack_container.find(".ks_dashboard_color_option").remove();
                    $ks_gridstack_container.find(".card-body").empty().append($("<div style='font-size:20px;'>Too many records for selected Chart Type. Consider using <strong>Domain</strong> to filter records or <strong>Record Limit</strong> to limit the no of records under <strong>30.</strong>"));
                    return;
                }
            }

            if (chart_data["ks_show_second_y_scale"] && item.ks_dashboard_item_type === 'ks_bar_chart') {
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
                                var ks_selection = chart_data.ks_selection;
                                if (ks_selection === 'monetary') {
                                    var ks_currency_id = chart_data.ks_currency;
                                    var ks_data = value;
                                    ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                                    ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                                   return ks_data;
                                } else if (ks_selection === 'custom') {
                                    var ks_field = chart_data.ks_field;
                                    return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                                } else {
                                   return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                                }
                            },
                        }
                    }
                ]
            }
            var chart_plugin = [];
            if (item.ks_show_data_value) {
                chart_plugin.push(ChartDataLabels);
            }
//            if (item.ks_data_label_type == 'value'){
////                Chart empty dataset fixed in last commit
//                if(chart_data.datasets.length > 0){
////                    for(let i=0;i<chart_data.datasets.length;i++){
////                        chart_data.datasets[i]["ks_data_label_type"] = 'value';
////                    }
//                    chart_data.datasets[0]["ks_data_label_type"] = 'value';
//                }
//            }
            var ksMyChart = new Chart($ksChartContainer[0], {
                type: chart_type === "area" ? "line" : chart_type,
                plugins: chart_plugin,
                data: {
                    labels: chart_data['labels'],
                    groupByIds: chart_data['groupByIds'],
                    domains: chart_data['domains'],
                    datasets: chart_data.datasets,
                },
                options: {
                    maintainAspectRatio: false,
                    responsiveAnimationDuration: 1000,
                    animation: {
                        easing: 'easeInQuad',
                    },
                   legend: {
                            display: item.ks_hide_legend
                        },
                    scales: scales,
                   layout: {
                        padding: {
                        bottom: 0,
                   }
                },
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
                        anchor: 'right',
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
                            if (item.ks_data_label_type == 'value'){
                                percentage = value;
                            }
                            return percentage;
                        },
                    },
                },

                }
            });

            this.chart_container[chart_id] = ksMyChart;
            if (chart_data && chart_data["datasets"].length > 0) self.ksChartColors(item.ks_chart_item_color, ksMyChart, chart_type, chart_family, item.ks_bar_chart_stacked, item.ks_semi_circle_chart, item.ks_show_data_value, chart_data, item);

        },

        ksHideFunction: function(options, item, ksChartFamily, chartType) {
            return options;
        },

        ksChartColors: function(palette, ksMyChart, ksChartType, ksChartFamily, stack, semi_circle, ks_show_data_value, chart_data, item) {
            var self = this;
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
                    if (ksMyChart.config.data.datasets[0]){
                        var datasets = ksMyChart.config.data.datasets[0];
                        var setsCount = datasets.data.length;
                    }
                    break;

                case "bar":
                case "horizontalBar":
                case "line":
                    if (ksMyChart.config.data.datasets[0]){
                        var datasets = ksMyChart.config.data.datasets;
                        var setsCount = datasets.length;
                    }
                    break;
            }

            //Calculate colors
//            var chartColors = [];
//
//            if (palette !== "default") {
//                //Get a sorted array of the gradient keys
//                var gradientKeys = Object.keys(gradient);
//                gradientKeys.sort(function(a, b) {
//                    return +a - +b;
//                });
//                for (var i = 0; i < setsCount; i++) {
//                    var gradientIndex = (i + 1) * (100 / (setsCount + 1)); //Find where to get a color from the gradient
//                    for (var j = 0; j < gradientKeys.length; j++) {
//                        var gradientKey = gradientKeys[j];
//                        if (gradientIndex === +gradientKey) { //Exact match with a gradient key - just get that color
//                            chartColors[i] = 'rgba(' + gradient[gradientKey].toString() + ')';
//                            break;
//                        } else if (gradientIndex < +gradientKey) { //It's somewhere between this gradient key and the previous
//                            var prevKey = gradientKeys[j - 1];
//                            var gradientPartIndex = (gradientIndex - prevKey) / (gradientKey - prevKey); //Calculate where
//                            var color = [];
//                            for (var k = 0; k < 4; k++) { //Loop through Red, Green, Blue and Alpha and calculate the correct color and opacity
//                                color[k] = gradient[prevKey][k] - ((gradient[prevKey][k] - gradient[gradientKey][k]) * gradientPartIndex);
//                                if (k < 3) color[k] = Math.round(color[k]);
//                            }
//                            chartColors[i] = 'rgba(' + color.toString() + ')';
//                            break;
//                        }
//                    }
//                }
//            } else {
//                for (var i = 0, counter = 0; i < setsCount; i++, counter++) {
//                    if (counter >= color_set.length) counter = 0; // reset back to the beginning
//
//                    chartColors.push(color_set[counter]);
//                }
//            }
            var chartColors = this.ks_chart_color_pallet(gradient, setsCount, palette, item);
            var datasets = ksMyChart.config.data.datasets;
            var options = ksMyChart.config.options;

            options.legend.labels.usePointStyle = true;
            if (ksChartFamily == "circle") {
                if (ks_show_data_value) {
                    options.legend.position = 'bottom';
                    options.layout.padding.top = 10;
                    options.layout.padding.bottom = 20;
                    options.layout.padding.left = 20;
                    options.layout.padding.right = 20;
                } else {
                    options.legend.position = 'top';
                }

                options = self.ksHideFunction(options, item, ksChartFamily, chartType);

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
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            k_amount = KsGlobalFunction.ks_monetary(k_amount, ks_currency_id);
                            return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            //                                                        ks_type = field_utils.format.char(ks_field);
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,item.ks_precision_digits]});
                            return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount + " " + ks_field;
                        } else {
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,item.ks_precision_digits]});
                            return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount
                        }
                    },
                    label: function(tooltipItem, data) {
                        return data.labels[tooltipItem.index];
                    },
                }
                for (var i = 0; i < datasets.length; i++) {
                    datasets[i].backgroundColor = chartColors;
                    datasets[i].borderColor = "rgba(255,255,255,1)";
                }
                if (semi_circle && (chartType === "pie" || chartType === "doughnut")) {
                    options.rotation = 1 * Math.PI;
                    options.circumference = 1 * Math.PI;
                }
            } else if (ksChartFamily == "square") {
                options = self.ksHideFunction(options, item, ksChartFamily, chartType);

                options.scales.xAxes[0].gridLines.display = false;
                options.scales.yAxes[0].ticks.beginAtZero = true;

                options.plugins.datalabels.align = 'end';

                options.plugins.datalabels.formatter = function(value, ctx) {
                    var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            var ks_data = value;
                            ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                           return ks_data;
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                        } else {
                           return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                        }
                };

                if (chartType === "line") {
                    options.plugins.datalabels.backgroundColor = function(context) {
                        return context.dataset.borderColor;
                    };
                }

                if (chartType === "horizontalBar") {
                    options.scales.xAxes[0].ticks.callback = function(value, index, values) {
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            var ks_data = value;
                            ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                           return ks_data;
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                        } else {
                           return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                        }
                    }
                    options.scales.xAxes[0].ticks.beginAtZero = true;
                } else {
                    options.scales.yAxes[0].ticks.callback = function(value, index, values) {
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            var ks_data = value;
                            ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                           return ks_data;
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                        } else {
                           return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                        }
                    }
                }

                options.tooltips.callbacks = {
                    label: function(tooltipItem, data) {
                        var ks_self = self;
                        var k_amount = data.datasets[tooltipItem.datasetIndex]['data'][tooltipItem.index];
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            k_amount = KsGlobalFunction.ks_monetary(k_amount, ks_currency_id);
                            return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            // ks_type = field_utils.format.char(ks_field);
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,item.ks_precision_digits]});
                            return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount + " " + ks_field;
                        } else {
                            k_amount = field_utils.format.float(k_amount, Float64Array,{digits:[0,item.ks_precision_digits]});
                            return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount
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
                                options.scales.xAxes[0].stacked = stack;
                                options.scales.yAxes[0].stacked = stack;
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
        },


        ksFetchChartItem: function(id) {
            var self = this;
            var item_data = self.ks_dashboard_data.ks_item_data[id];

            return self._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_item',
                args: [
                    [item_data.id], self.ks_dashboard_id, self.ksGetParamsForItemFetch(id)
                ],
                context: self.getContext(),
            }).then(function(new_item_data) {
                this.ks_dashboard_data.ks_item_data[id] = new_item_data[id];
                $(self.$el.find(".grid-stack-item[gs-id=" + id + "]").children()[0]).find(".card-body").empty();
                var item_data = self.ks_dashboard_data.ks_item_data[id]
                if (item_data.ks_list_view_data) {
                    var item_view = $(self.$el.find(".grid-stack-item[gs-id=" + id + "]").children()[0]);
                    var $container = self.renderListViewData(item_data);
                    item_view.find(".card-body").append($container);
                    var ks_length = JSON.parse(item_data['ks_list_view_data']).data_rows.length
                    if (new_item_data["ks_list_view_type"] === "ungrouped" && JSON.parse(item_data['ks_list_view_data']).data_rows.length) {
                        item_view.find('.ks_pager').removeClass('d-none');
                        if (item.ks_record_count <= item.ks_pagination_limit) item_view.find('.ks_load_next').addClass('ks_event_offer_list');
                        item_view.find('.ks_value').text("1-" + JSON.parse(item_data['ks_list_view_data']).data_rows.length);
                    } else {
                        item_view.find('.ks_pager').addClass('d-none');
                    }
                } else {
                    self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + id + "]").children()[0]), item_data);
                }
            }.bind(this));
        },



        _ksRenderNoItemView: function() {
            $('.ks_dashboard_items_list').remove();
            var self = this;
            $(QWeb.render('ksNoAIItemView')).appendTo(self.$el);
            $(".modal-body .ks_dashboard_ninja").height('200px');
            $('#ks_ai_add_all_item').addClass("d-none");

        },


        ks_get_current_gridstack_config: function(){
            var self = this;
            if (document.querySelector('.grid-stack') && document.querySelector('.grid-stack').gridstack){
                var items = document.querySelector('.grid-stack').gridstack.el.gridstack.engine.nodes;
            }
            var grid_config = {}


            if (items){
                for (var i = 0; i < items.length; i++) {
                    grid_config[items[i].id] = {
                        'x': items[i].x,
                        'y': items[i].y,
                        'w': items[i].w,
                        'h': items[i].h,
                    }
                }
            }
            return grid_config;
        },





        _renderListView: function(item, grid) {
            var self = this;
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }

            var list_view_data = JSON.parse(item.ks_list_view_data),
                pager = true,
                item_id = item.id,
                data_rows = list_view_data.data_rows,
                length = data_rows ? data_rows.length: false,
                item_title = item.name,
                ks_info = ks_description;
            var $ksItemContainer = self.renderListViewData(item);
            var  ks_data_calculation_type = self.ks_dashboard_data.ks_item_data[item_id].ks_data_calculation_type
            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_list_view_container', {
                ks_chart_title: item_title,
                ksIsDashboardManager: self.ks_dashboard_data.ks_dashboard_manager,
                ksIsUser: true,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                item_id: item_id,
                count: '1-' + length,
                offset: 1,
                intial_count: length,
                ks_pager: pager,
                calculation_type: ks_data_calculation_type,
                ks_info: ks_info,
                ks_company:item.ks_company

            })).addClass('ks_dashboarditem_id');

            if (item.ks_pagination_limit < length  ) {
                $ks_gridstack_container.find('.ks_load_next').addClass('ks_event_offer_list');
            }
            if (length < item.ks_pagination_limit ) {
                $ks_gridstack_container.find('.ks_load_next').addClass('ks_event_offer_list');
            }
            if (item.ks_record_data_limit === item.ks_pagination_limit){
                   $ks_gridstack_container.find('.ks_load_next').addClass('ks_event_offer_list');
            }
            if (length == 0){
                $ks_gridstack_container.find('.ks_pager').addClass('d-none');
            }
            if (item.ks_pagination_limit==0){
            $ks_gridstack_container.find('.ks_pager_name').addClass('d-none');
            }

            $ks_gridstack_container.find('.card-body').append($ksItemContainer);
            if (item.ks_data_calculation_type === 'query' || item.ks_list_view_type === "ungrouped"){
                $ks_gridstack_container.find('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
            }
            item.$el = $ks_gridstack_container;
            if (item_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[item_id].x, y:self.gridstackConfig[item_id].y, w:self.gridstackConfig[item_id].w, h:self.gridstackConfig[item_id].h, autoPosition:true, minW:3, maxW:null, minH:3, maxH:null, id:item_id});
                }
                else{
                    grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[item_id].x, y:self.gridstackConfig[item_id].y, w:self.gridstackConfig[item_id].w, h:self.gridstackConfig[item_id].h, autoPosition:false, minW:3, maxW:null, minH:3, maxH:null, id:item_id});
                }
            } else {
                grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:5, h:4, autoPosition:true, minW:4, maxW:null, minH:3, maxH:null, id:item_id});
            }
            $(document.querySelector(".modal-body .ks_dashboard_item_button_container")).remove();
            $(document.querySelector(".modal-body .ks_pager_name")).remove();
        },

        renderListViewData: function(item) {
            var self = this;
            var list_view_data = JSON.parse(item.ks_list_view_data);
            var item_id = item.id,
                data_rows = list_view_data.data_rows,
                item_title = item.name;
            if (item.ks_list_view_type === "ungrouped" && list_view_data) {
                if (list_view_data.date_index) {
                    var index_data = list_view_data.date_index;
                    for (var i = 0; i < index_data.length; i++) {
                        for (var j = 0; j < list_view_data.data_rows.length; j++) {
                            var index = index_data[i]
                            var date = list_view_data.data_rows[j]["data"][index]
                            if (date) {
                                if (list_view_data.fields_type[index] === 'date'){
                                    list_view_data.data_rows[j]["data"][index] = moment(new Date(date)).format(this.date_format) , {}, {timezone: false};
                                }else{
                                    list_view_data.data_rows[j]["data"][index] = moment(new Date(date+" UTC")).format(this.datetime_format), {}, {timezone: false};
                                }
                            }else{
                                list_view_data.data_rows[j]["data"][index] = "";
                            }
                        }
                    }
                }
            }
            if (list_view_data) {
                for (var i = 0; i < list_view_data.data_rows.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
                        if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
                            if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
                                list_view_data.data_rows[i].data[j] = field_utils.format.float(list_view_data.data_rows[i].data[j], Float64Array, {digits:[0,item.ks_precision_digits]})
                            }
                        } else {
                            list_view_data.data_rows[i].data[j] = "";
                        }
                    }
                }
            }
            var $ksItemContainer = $(QWeb.render('ks_list_view_table', {
                list_view_data: list_view_data,
                item_id: item_id,
                list_type: item.ks_list_view_type,
                isDrill: self.ks_dashboard_data.ks_item_data[item_id]['isDrill']
            }));
            self.list_container = $ksItemContainer;
            if (list_view_data){
                var $ksitemBody = self.ksListViewBody(list_view_data,item_id)
                self.list_container.find('.ks_table_body').append($ksitemBody)
            }
            if (item.ks_list_view_type === "ungrouped") {
                $ksItemContainer.find('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
            }

            if (!item.ks_show_records) {
                $ksItemContainer.find('#ks_item_info').hide();
            }
            return $ksItemContainer
        },

        ksListViewBody: function(list_view_data, item_id) {
            var self = this;
            var itemid = item_id
            var  ks_data_calculation_type = self.ks_dashboard_data.ks_item_data[item_id].ks_data_calculation_type;
            var list_view_type = self.ks_dashboard_data.ks_item_data[item_id].ks_list_view_type
            var $ksitemBody = $(QWeb.render('ks_list_view_tmpl', {
                        list_view_data: list_view_data,
                        item_id: itemid,
                        calculation_type: ks_data_calculation_type,
                        isDrill: self.ks_dashboard_data.ks_item_data[item_id]['isDrill'],
                        list_type: list_view_type,
                    }));
            return $ksitemBody;

        },
        renderKpi: function(item, grid) {
            var self = this;
            var field = item;
            var ks_date_filter_selection = field.ks_date_filter_selection;
            if (field.ks_date_filter_selection === "l_none") ks_date_filter_selection = self.ks_dashboard_data.ks_date_filter_selection;
            var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
            var kpi_data = JSON.parse(field.ks_kpi_data);
            var count_1 = kpi_data[0] ? kpi_data[0].record_data: undefined;
            var count_2 = kpi_data[1] ? kpi_data[1].record_data : undefined;
            var target_1 = kpi_data[0].target;
            var target_view = field.ks_target_view,
                pre_view = field.ks_prev_view;
            var ks_rgba_background_color = self._ks_get_rgba_format(field.ks_background_color);
            var ks_rgba_button_color = self._ks_get_rgba_format(field.ks_button_color);
            var ks_rgba_font_color = self._ks_get_rgba_format(field.ks_font_color);
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
            if (field.ks_previous_period && ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0) {
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
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
            item['ksIsDashboardManager'] = self.ks_dashboard_data.ks_dashboard_manager;

            item['ksIsUser'] = true;
            if (item.ks_tv_play){
                item['ksIsUser'] = false;
            }
            var ks_icon_url;
            if (field.ks_icon_select == "Custom") {
                if (field.ks_icon[0]) {
                    ks_icon_url = 'data:image/' + (self.file_type_magic_word[field.ks_icon[0]] || 'png') + ';base64,' + field.ks_icon;
                } else {
                    ks_icon_url = false;
                }
            }
//            parseInt(Math.round((count_1 / target_1) * 100)) ? field_utils.format.integer(Math.round((count_1 / target_1) * 100)) : "0"
            var target_progress_deviation = String(Math.round((count_1  / target_1) * 100));
             if(field.ks_multiplier_active){
                var target_progress_deviation = String(Math.round(((count_1 * field.ks_multiplier) / target_1) * 100));
             }
            var ks_rgba_icon_color = self._ks_get_rgba_format(field.ks_default_icon_color)
            var item_info = {
                item: item,
                id: field.id,
                count_1: KsGlobalFunction.ksNumFormatter(kpi_data[0]['record_data'], 1),
                count_1_tooltip: kpi_data[0]['record_data'],
                count_2: kpi_data[1] ? String(kpi_data[1]['record_data']) : false,
                name: field.name ? field.name : field.ks_model_id.data.display_name,
                target_progress_deviation:target_progress_deviation,
                icon_select: field.ks_icon_select,
                default_icon: field.ks_default_icon,
                icon_color: ks_rgba_icon_color,
                target_deviation: deviation,
                target_arrow: acheive ? 'up' : 'down',
                ks_enable_goal: field.ks_goal_enable,
                ks_previous_period: ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0 ? field.ks_previous_period : false,
                target: KsGlobalFunction.ksNumFormatter(target_1, 1),
                previous_period_data: previous_period_data,
                pre_deviation: pre_deviation,
                pre_arrow: pre_acheive ? 'up' : 'down',
                target_view: field.ks_target_view,
                pre_view: field.ks_prev_view,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                ks_icon_url: ks_icon_url,
                ks_rgba_button_color:ks_rgba_button_color,
                ks_info: ks_description,

            }

            if (item_info.target_deviation === Infinity) item_info.target_arrow = false;
            item_info.target_progress_deviation = parseInt(item_info.target_progress_deviation) ? field_utils.format.integer(parseInt(item_info.target_progress_deviation)) : "0"
            if (field.ks_multiplier_active){
                item_info['count_1'] = KsGlobalFunction._onKsGlobalFormatter(kpi_data[0]['record_data'] * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                item_info['count_1_tooltip'] = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
                item_info['count_1'] = KsGlobalFunction._onKsGlobalFormatter(kpi_data[0]['record_data'], field.ks_data_formatting, field.ks_precision_digits);
            }
            item_info['target'] = KsGlobalFunction._onKsGlobalFormatter(kpi_data[0].target, field.ks_data_formatting, field.ks_precision_digits);
            if (field.ks_unit){
            if (field.ks_multiplier_active){
            var ks_record_count = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
            var ks_record_count = kpi_data[0]['record_data']
            }
            var ks_selection = field.ks_unit_selection;
            if (ks_selection === 'monetary') {
            var ks_currency_id = field.ks_currency_id;
            var ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
            item_info['count_1'] = ks_data;
            } else if (ks_selection === 'custom') {
            var ks_field = field.ks_chart_unit;
            item_info['count_1']= ks_field+" "+KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            }else {
            item_info['count_1']= KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            }
            }
            var $kpi_preview;
            if (!kpi_data[1]) {
                if (field.ks_target_view === "Number" || !field.ks_goal_enable) {
                    $kpi_preview = $(QWeb.render("ks_kpi_template", item_info));
                } else if (field.ks_target_view === "Progress Bar" && field.ks_goal_enable) {
                    $kpi_preview = $(QWeb.render("ks_kpi_template_3", item_info));
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
                if (field.ks_previous_period && String(previous_period_data) && ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0) {
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
                if ($kpi_preview.find('.ks_target_previous').children().length !== 2) {
                    $kpi_preview.find('.ks_target_previous').addClass('justify-content-center');
                }
            }
//            $kpi_preview.find('.ks_dashboarditem_id').css({
//                "background-color": ks_rgba_background_color,
//                "color": ks_rgba_font_color,
//            });
            this.ks_kpi_preview_background_style($kpi_preview, ks_rgba_background_color, ks_rgba_font_color, field);
            if (field.ks_previous_period && String(previous_period_data) && ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0 &&
            (field.ks_goal_enable && field.ks_target_view === "Progress Bar")){
                  $kpi_preview.addClass('ks_previous_period')
            }

            return $kpi_preview

        },

        ks_kpi_preview_background_style: function($kpi_preview, ks_rgba_background_color, ks_rgba_font_color, field){
            $kpi_preview.find('.ks_dashboarditem_id').css({
                "background-color": ks_rgba_background_color,
                "color": ks_rgba_font_color,
            });
        },

        onkschartcontainerclick(ev){
            if($(ev.currentTarget).hasClass('ks_dashboard_kpi_dashboard')){
                if(!($(ev.currentTarget).parent().hasClass('ks_img_selected'))){
                    $('#ks_ai_add_item').removeClass("d-none");
                    $(ev.currentTarget).parent().addClass('ks_img_selected');
                    $(ev.currentTarget).find(".ks_img_display").removeClass("d-none");
                    this.ksSelectedgraphid.push(parseInt($(ev.currentTarget).parent()[0].id));
                }else{
                    $(ev.currentTarget).parent().removeClass('ks_img_selected');
                    $(ev.currentTarget).find(".ks_img_display").addClass("d-none")
                    const index = this.ksSelectedgraphid.indexOf(parseInt($(ev.currentTarget).parent()[0].id));
                    this.ksSelectedgraphid.splice(index, 1);
                }
            }else{
                if(!($(ev.currentTarget).hasClass('ks_img_selected'))){
                    $('#ks_ai_add_item').removeClass("d-none");
                    $(ev.currentTarget).addClass('ks_img_selected');
                    $(ev.currentTarget).find(".ks_img_display").removeClass("d-none");
                    this.ksSelectedgraphid.push(parseInt($(ev.currentTarget).parent()[0].id));
                }else{
                    $(ev.currentTarget).removeClass('ks_img_selected');
                    $(ev.currentTarget).find(".ks_img_display").addClass("d-none")
                    const index = this.ksSelectedgraphid.indexOf(parseInt($(ev.currentTarget).parent()[0].id));
                    this.ksSelectedgraphid.splice(index, 1);
                }
            }

            if (this.ksSelectedgraphid.length == 0){
                $('#ks_ai_add_item').addClass("d-none")
            }
        },
        onselectallitems:function(){
            this.ksSelectedgraphid = []
            document.querySelectorAll(".modal-body .ks_list_view_container").forEach((item) =>{
                $(item).addClass('ks_img_selected')
                $('.ks_img_display').removeClass("d-none");
                this.ksSelectedgraphid.push(parseInt($(item).parent()[0].id))
            });
            document.querySelectorAll(".modal-body .ks_dashboard_kpi_dashboard").forEach((item) =>{
                $(item).parent().addClass('ks_img_selected')
                $('.ks_img_display').removeClass("d-none");
                this.ksSelectedgraphid.push(parseInt($(item).parent()[0].id))
            });


            document.querySelectorAll(".modal-body .ks_dashboarditem_chart_container").forEach((item) =>{
                $(item).addClass('ks_img_selected')
                $('.ks_img_display').removeClass("d-none");
                this.ksSelectedgraphid.push(parseInt($(item).parent()[0].id))
            });

            $('#ks_ai_add_item').removeClass("d-none")
            $('#ks_ai_remove_all_item').removeClass("d-none")
            $('#ks_ai_add_all_item').addClass("d-none")
        },
        onremoveallitems: function(){
            _.each($('.ks_list_view_container'), function(selected_graph) {
                $(selected_graph).removeClass('ks_img_selected');
                $('.ks_img_display').addClass("d-none");
            });
            _.each($('.ks_dashboard_kpi_dashboard'), function(selected_graph) {
                $(selected_graph).parent().removeClass('ks_img_selected');
                $('.ks_img_display').addClass("d-none");
            });

            _.each($('.ks_dashboarditem_chart_container'), function(selected_graph) {
                $(selected_graph).removeClass('ks_img_selected');
                $('.ks_img_display').addClass("d-none");
            });
            this.ksSelectedgraphid = [];
             $('#ks_ai_add_item').addClass("d-none")
             $('#ks_ai_remove_all_item').addClass("d-none")
             $('#ks_ai_add_all_item').removeClass("d-none")
        },


        onKsaddItemClick: function(e) {
            var self = this;
            var dashboard_id = this.ks_ai_dash_id;
            var dashboard_name = this.ks_ai_dash_name;
            this._rpc({
                model: 'ks_dashboard_ninja.item',
                method: 'write',
                args: [this.ksSelectedgraphid, {
                    'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
                }],
            }).then(function(result) {
                self.displayNotification({
                    title:_t("Items added"),
                    message:_t('Items are added to ' + dashboard_name + ' .'),
                    type: 'success',
                });
                $.when(self.ks_fetch_data()).then(function() {
                    self.onksaideletedash();
                });
            });
        },
        onksaideletedash:function(){
        var self= this;
        this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'unlink',
                args: [this.ks_ai_del_id],
            }).then(function(result){
                 window.location.reload();
            });

        },

    });

    core.action_registry.add('ks_dashboard_ninja_ai', KsAIDashboardNinja);


    return KsAIDashboardNinja;
});