
let update_timer = null;
let update_list = [];

function show_error_from_api(data) {
    if  (data) {
        if (data.responseJSON) {
            if (data.responseJSON.detail) {
                toastr.error(data.responseJSON.detail);
                return;
            }
        }
        if (data.status && data.statusText) {
            toastr.error(`An error occurred! ${data.statusText} (status code ${data.status}).`);
            return;
        }
    }
    toasr.error("An unknown exception occurred");
}

function create_element(tag_name, class_list, text) {
    let element = document.createElement(tag_name);
    for (let i = 0; i < class_list.length; i++) {
        element.classList.add(class_list[i]);
    }
    element.appendChild(document.createTextNode(text));
    return element;
}

function set_cookie(name,value,days) {
    let expires = "";
    value = encodeURI(value);
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

function get_cookie(name) {
    let nameEQ = name + "=";
    let ca = document.cookie.split(';');
    for(let i=0;i < ca.length;i++) {
        let c = ca[i];
        while (c.charAt(0)===' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) === 0) return decodeURI(c.substring(nameEQ.length,c.length));
    }
    return null;
}

function set_list_cookie(name, list, days) {
	try {
		let string = JSON.stringify(list);
		set_cookie(name, string, days);
	    return true;
	}
	catch(error) {
        return false;
    }
}

function post_and_callback_with_error(data_url, data, callback, callback_error/*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    data.csrfmiddlewaretoken = get_csrf_token();
    data = JSON.stringify(data);
    fetch(
        data_url,
        {
            method: "POST",
            body: data,
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": get_csrf_token(),
            }
        }
    ).then(response => {
        args.unshift(response);
        callback.apply(this, args);
    }).catch(error => {
        args.unshift(error);
        callback_error.apply(this, args);
    });
}

function delete_and_callback(data_url, data, callback/*, args*/) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let headers = {"X-CSRFToken": get_csrf_token()};
        $.ajax({type: 'DELETE', url: data_url, data, dataType:'json', asynch: true, headers: headers, success:
            function(data) {
                args.unshift(data);
                callback.apply(this, args);
            }}).fail(function() {
                console.error("Error")
            });
        }
    )
}

function get_and_callback(data_url, data, callback/*, args */) {
    let args = Array.prototype.slice.call(arguments, 4);
    jQuery(function($) {
        let headers = {"X-CSRFToken": get_csrf_token()};
        $.ajax({type: 'GET', url: data_url, data, dataType:'json', asynch: true, headers: headers, success:
            function(data) {
                if (data.error) {
                    console.error(data.error);
                }
                else {
                    args.unshift(data);
                    callback.apply(this, args);
                }
            }}).fail(function() {
                console.error("Error")
            });
        }
    )
}

function replace_container(container, data) {
    container.innerHTML = data;
}

function add_update_list(func, args) {
    update_list.push({func: func, args: args});
}

function update_update_list() {
    clearTimeout(update_timer);
    for (let i = 0; i < update_list.length; i++) {
        update_list[i].func.apply(this, update_list[i].args);
    }
    update_timer = setTimeout(update_update_list, 5000);
}

function get_csrf_token() {
    let cookie_csrf = get_cookie("csrf_token");
    if (cookie_csrf === null) {
        if (typeof CSRF_TOKEN !== 'undefined') {
            return CSRF_TOKEN;
        }
        else {
            throw "Unable to retrieve CSRF token";
        }
    }
    else {
        return cookie_csrf;
    }
}

$(document).ready(function() {
    update_update_list();
});