// Hello, I have no idea what I did, but it works.

/*
 / \\__
(    @\\___
/         O
/   (_____/
/_____/   U
*/

$(document).ready(function() {
    $('#search-bar').focus();

    $('#summaries-search-button').click(performSearch);
    $('#search-bar').keypress(function(event) {
        performSearch();
        if (event.keyCode === 13) {
            event.preventDefault();
        }
    });

    function performSearch() {
        const searchTerm = $('#search-bar').val().trim().toLowerCase();

        if (searchTerm === "") {
            $(".course-name").closest("tr").show();
        } else {
            $(".course-name").each(function() {
                const courseName = $(this).text().toLowerCase();
                if (courseName.includes(searchTerm)) {
                    $(this).closest("tr").show();
                } else {
                    $(this).closest("tr").hide();
                }
            });
        }
    }
});
