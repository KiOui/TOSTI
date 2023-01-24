
let update_timer = null;
let refresh_list = {};
let lastRefresh = null;

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

function debounce(func, timeout = 300){
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => { func.apply(this, args); }, timeout);
  };
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
        if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length,c.length));
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

function remove_refresh_url(url, assigner_func) {
    if (refresh_list[url]) {
        const index = refresh_list[url].indexOf(assigner_func);
        if (index >= 0) {
            refresh_list[url].splice(index, 1);
            if (refresh_list[url].length === 0) {
                delete refresh_list[url];
            }
        }
    }
}

function update_refresh_list() {
    clearTimeout(update_timer);
    Promise.all(Object.entries(refresh_list).map(([key, value]) => {
        return fetch(
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
    })).finally(() => {
        lastRefresh = (new Date()).getTime();
        update_timer = setTimeout(update_refresh_list, 5000);
    });
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

function visibilityChange(event) {
    if (event.target.hidden) {
        clearTimeout(update_timer);
    } else {
        clearTimeout(update_timer);
        if (lastRefresh === null || (new Date()).getTime() - lastRefresh > 5000) {
            update_refresh_list();
        } else {
            update_timer = setTimeout(update_refresh_list, 5000);
        }
    }
}

update_refresh_list();
document.addEventListener("visibilitychange", visibilityChange);