/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('odoo_new_tab.ListRenderer', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    ListRenderer.rowsTemplate = "web.ListRenderer.Rows"

    ListRenderer.include({
        _onRowClicked: function (event) {
            var a_td = $(event.target).closest('.oe_new_tab_col');
            if (a_td.length) {
                event.stopPropagation();
            } else {
                return this._super(event);
            }
        },


        _renderHeader: function () {
            var $thead = this._super();
            if (!this.arch.editable) {
                if (this.hasSelectors) {
                    $thead.find('.o_list_record_selector').after(this._renderNewTab('th', '#'));
                } else {
                    $thead.find('tr').prepend(this._renderNewTab('th', '#'));
                }
            }
            return $thead;
        },
        
        _renderRow: function (record) {
            var $tr = this._super(record);
            if (!this.arch.editable) {
                var rec_id = record.data.id;
                var model = record.model;
                var $a = $('<a>');
                var url = 'web#id=' + rec_id + '&view_type=form';
                if (model) {
                    url += '&model=' + model;
                }
                if (record.context.params) {
                    if (record.context.params.menu_id) {
                        url += '&menu_id=' + record.context.params.menu_id;
                    }
                    if (record.context.params.action) {
                        url += '&action=' + record.context.params.action;
                    }
                }
                $a.attr('href', url)
                    .attr('target', '_blank')
                    .append($('<i>').addClass('fa fa-external-link'));
                if (this.hasSelectors) {
                    $tr.find('.o_list_record_selector').after(this._renderNewTab('td', $a));
                } else {
                    $tr.prepend(this._renderNewTab('td', $a))
                }
            }
            return $tr;
        },

        _renderNewTab: function (tag, content) {
            return $('<' + tag + '>')
                .addClass('oe_new_tab_col')
                .append(content);
        },

        _getNumberOfCols: function () {
            var cols = this._super();
            if (!this.arch.editable) {
                cols++;
            }
            return cols;
        },

        _renderFooter: function () {
            var $cells = this._super();
            if (!this.arch.editable) {
                $cells.find('tr').prepend($('<td>'));
            }
            return $cells;
        },

        _renderGroupRow: function (group, groupLevel) {
            var $grp_tr = this._super(group, groupLevel);
            if (!this.arch.editable) {
                $grp_tr.find('th').after($('<td>'));
            }
            return $grp_tr
        },
    });
});
