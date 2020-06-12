let typingTimer;
let typingInterval = 200;

let current_search_index = 0;

function construct_list(data) {

}

function update_search_list(data) {
	RESULT_FIELD.innerHTML = construct_list(data);
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
            if (data.id === current_search_index && search === data.query) {
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
		typeof(SEARCH_URL) !== 'undefined') {
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