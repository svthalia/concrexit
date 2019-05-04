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

    var input = document.querySelector('#id_address_street');
    var autocomplete = new google.maps.places.Autocomplete(input);
    autocomplete.addListener('place_changed', function () {
        var place = autocomplete.getPlace();

        var getAddressItem = function(type, length) {
            var address = place.address_components;
            var addressItem = address.find(function (item) {
                return item.types.includes(type);
            });
            var key = length + '_name';
            return addressItem && addressItem[key] ? addressItem[key] : '';
        };

        $('#id_address_street').val(
            getAddressItem('route', 'long') + ' '
            + getAddressItem('street_number', 'long'));

        $('#id_address_city').val(
            getAddressItem('locality', 'long'));

        $('#id_address_postal_code').val(
            getAddressItem('postal_code', 'long'));

        $('#id_address_country').val(
            getAddressItem('country', 'short').toUpperCase());
    });
});
