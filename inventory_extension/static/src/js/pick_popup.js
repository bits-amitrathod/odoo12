odoo.define('inventory_extension.pick_popup', function (require) {
    'use strict';

    var rpc = require('web.rpc');

    $(window).on('hashchange', function() {
        var url_loader = window.location.href;

        if (url_loader.includes('model=stock.picking&view_type=form')) {
            var pickingId = url_loader.split('id=')[1].split('&')[0];

            // Retrieve the picking_warn_msg and customer_id using an RPC call
            rpc.query({
                model: 'stock.picking',
                method: 'read',
                args: [[parseInt(pickingId)], ['picking_warn_msg', 'partner_id','is_online']],
            }).then(function (result) {
                var pickingWarnMsg = result[0].picking_warn_msg || '';
                var customerId = result[0].partner_id ? result[0].partner_id[0] : '';

                if (customerId && result[0].is_online) {
                    rpc.query({
                        model: 'res.partner',
                        method: 'read',
                        args: [[customerId], ['picking_warn']],
                    }).then(function (partnerResult) {
                        var partnerPickingWarn = partnerResult[0].picking_warn || '';

                        if (pickingWarnMsg || partnerPickingWarn === 'block') {
                            var customerName = result[0].partner_id ? result[0].partner_id[1] : '';

                            var popupHtml = '<div id="popup" class="modal o_legacy_dialog o_technical_modal show" style="position: fixed;left: 16px;top: 42px;right: 0;transform: translate(-1%, -5%);width: 100%;height: 100%;display: flex; justify-content: center;align-items: center;background-color: rgba(0, 0, 0, 0.5);data-backdrop : static;tabindex=-1;overflow-x: hidden;">';
                            popupHtml += '<div style="width: 985px;height: 185px;background-color: #fff;border-radius: 0px;padding: -17px;box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);position: relative;bottom: 36%;padding-top: 65px;padding-bottom: 128px;"><button type="button" id="closeButton" class="close" data-original-title="" title="" style="padding-right: 20px;position: relative;bottom: 48px;">';
                            popupHtml += '<button type="button" id="closeButton" class="close" data-original-title="" title="" style="padding-right: 20px;position: relative;bottom: 48px;"><span>&times;</span></button>';
                            popupHtml += '<h3 style="margin-top: -48px;padding-left: 20px;">Warning for ' + customerName + '</h3>';
                            popupHtml += '<hr>';
                            popupHtml += '<p style="padding: 15px 15px 15px 20px;;">' + pickingWarnMsg + '</p>';
                            popupHtml += '<hr>';
                            popupHtml += '<div style="display: flex; justify-content: flex-start; margin-top: 20px;">';
                            popupHtml += '<button type="button" style="padding-left: 20px"; id="okButton" class="btn btn-secondary" data-original-title="" title=""><span>Ok</span></button>';
                            popupHtml += '</div>';
                            popupHtml += '</div>';
                            popupHtml += '</div>';

                            $('body').append(popupHtml);

                            $(document).on('click', '#okButton', function () {
                                console.log('OK button clicked');
                                // Perform OK button action here
                                $('#popup').remove();
                            });

                            $(document).on('click', '#closeButton', function () {
                                console.log('Close button clicked');
                                // Perform Close button action here
                                $('#popup').remove();
                            });
                        }
                    });
                }
            });
        }
    });
});
