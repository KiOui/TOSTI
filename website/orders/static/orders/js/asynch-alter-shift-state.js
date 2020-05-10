
function send_post_toggle(data_url, csrf_token, callback, active/*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
            'active': active
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    console.error(data.error);
                }
                else {
                    args.unshift(data);
                    callback.apply(this, args);
                }
            }}).fail(function() {
                console.error("Error while toggling shift state.")
            });
        }
    )
}

function send_post(data_url, csrf_token, callback/*, args */) {
    let args = Array.prototype.slice.call(arguments, 3);
    jQuery(function($) {
        let data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.ajax({type: 'POST', url: data_url, data, dataType:'json', asynch: true, success:
            function(data) {
                if (data.error) {
                    console.error(data.error);
                }
                else {
                    args.unshift(data);
                    callback.apply(this, args);
                }
            }}).fail(function() {
                console.error("Error while getting order data.");
            });
        }
    )
}

function update_toggle(data, element) {
    if (data.active) {
        element.classList.remove(['bg-danger']);
        element.classList.add('bg-success');
    }
    else {
        element.classList.remove(['bg-success']);
        element.classList.add('bg-danger');
    }
}

function toggle_shift_activation(element) {
    send_post_toggle(TOGGLE_SHIFT_URL, CSRF_TOKEN, update_toggle, element.classList.contains('bg-danger'), element);
}

function add_time() {
    send_post(ADD_TIME_URL, CSRF_TOKEN, succeeded_add_time);
}

function add_capacity() {
    send_post(ADD_CAPACITY_URL, CSRF_TOKEN, succeeded_add_capacity);
}

function succeeded_add_time(data) {
    SUCCESS_CONTAINER.innerHTML = "Added 5 minutes to the end time of this shift";
    SUCCESS_CONTAINER.style.display = "";
    update_page();
}

function succeeded_add_capacity(data) {
    SUCCESS_CONTAINER.innerHTML = "Added 5 capacity to this shift";
    SUCCESS_CONTAINER.style.display = "";
    update_page();
}

function update_page() {
    if (typeof(update_header) !== 'undefined') {
        update_header();
    }
    if (typeof(update_footer) !== 'undefined') {
        update_footer();
    }
}

$(document).ready(function() {
    if (!(typeof(SUCCESS_CONTAINER) !== 'undefined' &&
        typeof(CSRF_TOKEN) !== 'undefined' &&
        typeof(TOGGLE_SHIFT_URL) !== 'undefined' &&
        typeof(ADD_TIME_URL) !== 'undefined' &&
        typeof(ADD_CAPACITY_URL) !== 'undefined')) {
        console.warn("One of the required javascript variables is not defined, footer buttons are disabled.")
    }
});