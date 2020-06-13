
function send_queue_post_update(data_url, callback/*, args */) {
    let args = Array.prototype.slice.call(arguments, 2);
    let csrf_token = get_cookie('csrftoken');
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

function replace_queue(header) {
    QUEUE_CONTAINER.innerHTML = header.data;
}

function update_queue() {
    send_queue_post_update(QUEUE_REFRESH_URL, replace_queue);
}

function update_queue_continuous() {
    update_queue();
    setTimeout(update_queue_continuous, 5000);
}

$(document).ready(function() {
    if (typeof(QUEUE_CONTAINER) !== 'undefined' &&
        typeof(QUEUE_REFRESH_URL) !== 'undefined') {
        update_queue_continuous();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic queue updates disabled.")
    }
});