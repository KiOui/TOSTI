
function send_header_post_update(data_url, csrf_token, callback/*, args */) {
    let args = Array.prototype.slice.call(arguments, 3);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                args.unshift(data);
                callback.apply(this, args);
            }}).fail(function() {
                console.error("Failed to update header");
            });
        }
    )
}

function replace_order_overview(order_overview) {
    ORDER_OVERVIEW_CONTAINER.innerHTML = order_overview.data;
}

function update_order_overview() {
    send_header_post_update(ORDER_OVERVIEW_REFRESH_URL, ORDER_OVERVIEW_CSRF_TOKEN, replace_order_overview);
}

function update_order_container_continuous() {
    update_order_overview();
    setTimeout(update_order_container_continuous, 5000);
}

$(document).ready(function() {
    if (typeof(ORDER_OVERVIEW_CONTAINER) !== 'undefined' &&
        typeof(ORDER_OVERVIEW_CSRF_TOKEN) !== 'undefined' &&
        typeof(ORDER_OVERVIEW_REFRESH_URL) !== 'undefined') {
        update_order_container_continuous();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic order overview updates disabled.")
    }
});