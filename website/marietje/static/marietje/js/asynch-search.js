let typingTimer;
let typingInterval = 200;

let current_search_index = 0;

function display_message(data) {
	MESSAGE_FIELD.innerHTML = "";
	if (data.error) {
		MESSAGE_FIELD.appendChild(create_element('p', ['alert', 'alert-danger'], data.msg));
	}
	else {
		MESSAGE_FIELD.appendChild(create_element('p', ['alert', 'alert-success'], data.msg));
	}
	if (typeof(update_queue) !== 'undefined') {
		update_queue();
	}
}

function add_to_queue(track_id, callback/*, args */) {
	let args = Array.prototype.slice.call(arguments, 2);
    let csrf_token = get_cookie('csrftoken');
	jQuery(function($) {
		let data = {
			'id': track_id,
            'csrfmiddlewaretoken': csrf_token
		};
		$.ajax({type: 'POST', url: ADD_URL, data, dataType:'json', asynch: true, success:
		function(data) {
			args.unshift(data);
			callback.apply(this, args);
		}}).fail(function() {
			console.log("Error while adding " + track_id + " to queue");
		});
	});
}

function update_search_list(data) {
	RESULT_FIELD.innerHTML = data;
}

function query(search, callback/*, args */) {
	let args = Array.prototype.slice.call(arguments, 2);
    let csrf_token = get_cookie('csrftoken');
	jQuery(function($) {
		current_search_index = current_search_index + 1;
		let data = {
			'maximum': 5,
			'query': search,
			'id': current_search_index,
            'csrfmiddlewaretoken': csrf_token
		};
		$.ajax({type: 'POST', url: SEARCH_URL, data, dataType:'json', asynch: true, success:
		function(data) {
            if (parseInt(data.id) === current_search_index && search === data.query) {
				args.unshift(data.result);
                callback.apply(this, args);
            }
		}}).fail(function() {
			console.log("Error while getting search results for query " + search);
		});
	});
}

$(document).ready(function() {
	if (typeof(QUERY_FIELD) !== 'undefined' &&
        typeof(RESULT_FIELD) !== 'undefined' &&
		typeof(SEARCH_URL) !== 'undefined' &&
		typeof(ADD_URL) !== 'undefined' &&
		typeof(MESSAGE_FIELD) !== 'undefined') {
		QUERY_FIELD.addEventListener('keyup', () => {
			clearTimeout(typingTimer);
			let inputted = QUERY_FIELD.value;
			if (inputted === "") {
				RESULT_FIELD.style.display = "none";
			} else {
				RESULT_FIELD.style.display = "";
			}

			if (QUERY_FIELD.value) {
				typingTimer = setTimeout(query.bind(null, inputted, update_search_list), typingInterval);
			}
		});
	}
	else {
		console.warn("One of the required javascript variables is not defined, searching is disabled.")
	}
});