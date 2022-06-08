function openThabloidFancybox(e, btn) {
    e.preventDefault();
    const downloadLink = btn.nextElementSibling.href;
    fetch(btn.href).then(response => response.json()).then((data) => {
        Fancybox.show(data, {
            Toolbar: {
                display: [
                    { id: "counter", position: "center" },
                    "download",
                    "close",
                ],
            },
            on : {
                load : (fancybox, carousel) => {
                    carousel.src = downloadLink;
                }
            }
        });
    });
}

window.onload = (event) => {
    mixitup('#thabloid-index', {
        selectors: {
            control: '.nav-link'
        }
    });
    document.querySelectorAll('#thabloid-index .thabloid-card .btn.open').forEach((btn) => btn.addEventListener("click", (e) => openThabloidFancybox(e, btn)));
}
