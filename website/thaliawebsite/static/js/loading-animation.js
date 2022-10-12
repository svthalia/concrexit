const items = document.querySelectorAll(".pulsing-background");
items.forEach(
    (item) => {
        item.querySelector("img").addEventListener(
            "load", event => {event.target.parentNode.classList.remove("pulsing-background")}
        )
    }
)

