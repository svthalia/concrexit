(jQuery || django.jQuery)(function () {
    $ = jQuery || django.jQuery;
    var signatureField = $('#id_signature');
    var signatureCanvas = document.getElementById("id_signature_canvas");
    var signaturePad = new SignaturePad(signatureCanvas);

    function canvasToField() {
        if (signaturePad.toData().length) {
            signatureField.val(signaturePad.toDataURL("image/svg+xml"));
        }
    }

    function resizeCanvas() {
        var ratio = Math.max(window.devicePixelRatio || 1, 1);
        signatureCanvas.width = signatureCanvas.offsetWidth * ratio;
        signatureCanvas.height = signatureCanvas.offsetHeight * ratio;
        signatureCanvas.getContext("2d").scale(ratio, ratio);
        signaturePad.clear(); // otherwise isEmpty() might return incorrect value
    }

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    signaturePad.onEnd = canvasToField;

    $('#canvas-undo-btn').click(function (e) {
        e.preventDefault();
        var data = signaturePad.toData();
        if (data) {
            data.pop();
            signaturePad.fromData(data);

            if (data.length) {
                canvasToField();
            } else {
                signatureField.val('');
            }
        }
    });

    $('#canvas-clear-btn').click(function (e) {
        e.preventDefault();
        signaturePad.clear();
        signatureField.val('');
    });

    var ddCheckbox = $('#id_direct_debit');

    function showDirectDebitFields() {
        if (ddCheckbox.is(':checked')) {
            $('.direct-debit-fields').removeClass('d-none');
            $('.normal-fields').addClass('col-lg-6');
        } else {
            $('.direct-debit-fields').addClass('d-none');
            $('.normal-fields').removeClass('col-lg-6');
        }
    }

    showDirectDebitFields();
    ddCheckbox.change(showDirectDebitFields);
});



