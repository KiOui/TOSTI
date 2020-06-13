
function send_post(url, callback) {
	let csrf_token = get_cookie('csrftoken');
	jQuery(function($) {
		let data = {
            'csrfmiddlewaretoken': csrf_token
		};
		$.ajax({type: 'POST', url: url, data, dataType:'json', asynch: true, success:
		function(data) {
			callback(data);
		}}).fail(function() {
			console.log("Error while adding performing action");
		});
	});
}

function refresh_if_ready(data) {
	if (typeof(replace_player) !== 'undefined') {
		replace_player(data);
	}
}
