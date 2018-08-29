odoo.define('WebsiteCstm.WebsiteCstm', function (require) {
    "use strict";
    require('web.dom_ready');
    $(document).ready(function() {
        $("[rel='tooltip']").tooltip();

        $('.thumbnail').hover(
            function() {
                $(this).find('.caption').fadeIn(250)
            },
            function() {
                $(this).find('.caption').fadeOut(205)
            }
        );
    });

    $(document).ready(function() {
        $('.search_autocomplete').devbridgeAutocomplete({
            serviceUrl: '/shop/get_suggest',
            onSelect: function (suggestion) {
                 window.location.replace(window.location.origin +
                    '/shop/product/' + suggestion.data.id + '?search=' + suggestion.value);
            }
        });
    });
});