/*global URLify*/

function slugName(str) {
    return str.replaceAll(" ", "-").toLowerCase()
}

// init
{
    const $ = django.jQuery;
    $("#id_title").on('keyup', function () {
        const slug = $("#id_slug");
        if (slug.data("_changed")) return;
        slug.val(slugName(this.value) + "-" + new Date().getFullYear())

        slug.data('_changed', false);
        slug.on('change', function () {
            slug.data('_changed', true);
        });
    });

}
