
function replace_footer(data, container) {
    if (data.status) {
        container.classList.remove('bg-danger');
        container.classList.add('bg-success');
    }
    else {
        container.classList.remove('bg-success');
        container.classList.add('bg-danger');
    }
}