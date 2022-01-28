(function () {
    const announcementClose = document.querySelectorAll(
        ".announcement .btn-close"
    );
    announcementClose.forEach((button) =>
        button.addEventListener("click", async () => {
            button.parentElement.parentNode.removeChild(button.parentElement);
            await fetch("/announcements/close-announcement", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": Cookies.get("csrftoken"),
                },
                body: "id=" + button.dataset["announcementId"],
            });
        })
    );
})();
