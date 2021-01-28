let typingTimer;

let current_search_index = 0;

function add_to_queue(track_id) {
    let csrf_token = get_cookie('csrftoken');
	jQuery(function($) {
		let data = {
			'id': track_id,
            'csrfmiddlewaretoken': csrf_token
		};
		$.ajax({type: 'POST', url: ADD_URL, data, asynch: true, success:
		function(data) {
			toastr.success("Track added to queue.");
			update_update_list();
		}}).fail(function() {
			toastr.error("Failed to add track to the queue, please try again later.");
		});
	});
}

function query() {
    let csrf_token = get_cookie('csrftoken');
	jQuery(function($) {
		current_search_index = current_search_index + 1;
		let data = {
			'query': player_search_vue.query,
			'id': current_search_index,
            'csrfmiddlewaretoken': csrf_token
		};
		$.ajax({type: 'GET', url: SEARCH_URL, data, dataType:'json', asynch: true, success:
		function(data) {
            if (parseInt(data.id) === current_search_index && player_search_vue.query === data.query) {
				player_search_vue.tracks = data.results;
            }
		}}).fail(function() {
			console.log("Error while getting search results for query " + search);
		});
	});
}

function set_search_timeout() {
    clearTimeout(typingTimer);
    if (player_search_vue.query !== "") {
        typingTimer = setTimeout(query, 200);
    }
}

function search_success(products) {
    player_search_vue.search_results = products;
}