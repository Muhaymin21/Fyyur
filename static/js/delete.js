window.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#delete_venue').addEventListener('click', e => {
        let r = confirm("Are you sure?");
        if (r === true) {
            delete_venu(e.target.dataset['id']);
        }
    });
});

function delete_venu(venue_id) {
    fetch('/venues/' + venue_id, {
        method: 'DELETE',
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    }).catch(err => {
        console.error(err);
    });
}
