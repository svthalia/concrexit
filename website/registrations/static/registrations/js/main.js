function changeVisiblity(value) {
    var bType = $('form').data('benefactor-type');
    if (value === bType) {
        $('#id_contribution').parent().removeClass('d-none');
        $('#id_length').parent().addClass('d-none');
        $('#id_length').val('year');
    } else {
        $('#id_contribution').parent().addClass('d-none');
        $('#id_length').parent().removeClass('d-none');
        $('#id_length').val('');
    }
}

$(function() {
    var membershipEl = $('select#id_membership_type');
    if (membershipEl.length !== 0) {
        changeVisiblity(membershipEl.val());

        membershipEl.change(function () {
            changeVisiblity(this.value);
        });
    }
});
