
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

function replace_header(header) {
    HEADER_CONTAINER.innerHTML = header.data;
}

function update_header() {
    send_header_post_update(HEADER_REFRESH_URL, HEADER_CSRF_TOKEN, replace_header);
}

function update_header_continuous() {
    update_header();
    setTimeout(update_header_continuous, 5000);
}

$(document).ready(function() {
    if (typeof(HEADER_CONTAINER) !== 'undefined' &&
        typeof(HEADER_CSRF_TOKEN) !== 'undefined' &&
        typeof(HEADER_REFRESH_URL) !== 'undefined') {
        update_header_continuous();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic header updates disabled.")
    }
});