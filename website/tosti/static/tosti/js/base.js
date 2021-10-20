
let update_timer = null;
let update_list = [];
let refresh_list = {};

async function show_error_from_api(data) {
    if (data) {
        try {
            let json = await data.json();
            if (json.detail) {
                tata.error('', json.detail);
                return;
            }
        } catch (error) {}
        try {
            if (data.status && data.statusText) {
                tata.error('', `An error occurred! ${data.statusText} (status code ${data.status}).`);
                return;
            }
        } catch (error) {}
    }
    tata.error('', "An unknown exception occurred, the server might be offline or not responding.");
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

function replace_container(container, data) {
    container.innerHTML = data;
}

function add_refresh_url(url, assigner_func) {
    if (refresh_list[url]) {
        refresh_list[url].push(assigner_func);
    } else {
        refresh_list[url] = [assigner_func];
    }
}

function update_refresh_list() {
    clearTimeout(update_timer);
    for (const [key, value] of Object.entries(refresh_list)) {
        fetch(
            key,
            {
                headers: {
                    "X-CSRFToken": get_csrf_token(),
                }
            }
        ).then(response => {
            if (response.status === 200) {
                return response.json();
            } else {
                throw response;
            }
        }).then(data => {
            for (let i = 0; i < value.length; i++) {
                try {
                    value[i].apply(this, [data]);
                } catch (error) {
                    console.log(`An error occurred while refreshing ${key} and executing function ${value[i]}. Error: ${error}`)
                }
            }
        }).catch(error => {
            console.log(`An error occurred while refreshing ${key}. Error: ${error}`)
        });
    }
    update_timer = setTimeout(update_refresh_list, 5000);
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

update_refresh_list();