
function send_player_post_update(data_url, csrf_token, callback/*, args */) {
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

function replace_player(header) {
    PLAYER_CONTAINER.innerHTML = header.data;
}

function update_player() {
    send_player_post_update(PLAYER_REFRESH_URL, PLAYER_CSRF_TOKEN, replace_player);
}

function update_player_continuous() {
    update_player();
    setTimeout(update_player_continuous, 5000);
}

$(document).ready(function() {
    if (typeof(PLAYER_CONTAINER) !== 'undefined' &&
        typeof(PLAYER_CSRF_TOKEN) !== 'undefined' &&
        typeof(PLAYER_REFRESH_URL) !== 'undefined') {
        update_player_continuous();
    }
    else {
        console.warn("One of the required javascript variables is not defined, automatic player updates disabled.")
    }
});