
function send_footer_post_data(data_url, csrf_token, callback/*, args */) {
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

function replace_footer(data) {
    if (data.status) {
        FOOTER_SHIFT_STATUS.classList.remove('bg-danger');
        FOOTER_SHIFT_STATUS.classList.add('bg-success');
    }
    else {
        FOOTER_SHIFT_STATUS.classList.remove('bg-success');
        FOOTER_SHIFT_STATUS.classList.add('bg-danger');
    }
}

function update_footer() {
    send_footer_post_data(FOOTER_REFRESH_URL, FOOTER_CSRF_TOKEN, replace_footer);
}

function update_footer_continuous() {
    update_footer();
    setTimeout(update_footer_continuous, 5000);
}

$(document).ready(function() {
    if (typeof(FOOTER_CSRF_TOKEN) !== 'undefined' &&
        typeof(FOOTER_REFRESH_URL) !== 'undefined' &&
        typeof(FOOTER_SHIFT_STATUS) !== 'undefined') {
        update_footer_continuous();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic header updates disabled.")
    }
});