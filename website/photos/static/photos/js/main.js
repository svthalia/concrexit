function setNumLikes(numLikes) {
    const counter = document.querySelector('.fancybox__button--numlikes')
    if (numLikes === 1) {
        counter.innerHTML = numLikes.toString() + " like";
    } else {
        counter.innerHTML = numLikes.toString() + " likes";
    }
}

function updateLikes(numLikes, userLikes) {
    const button = document.querySelector('.fancybox__button--like')

    if (userLikes) {
        button.classList.add('liked')
    } else {
        button.classList.remove('liked')
    }
    setNumLikes(numLikes);
}

function getLikeStatus(slide) {
    let numLikes = slide.numLikes;
    let userLikes = false;

    fetch(slide.likeurl).then(response => response.json()).then(data => {
        numLikes = data.num_likes;
        userLikes = data.liked;
        updateLikes(numLikes, userLikes);
    }).catch();
    slide.numLikes = numLikes;
}

function toggleLike(slide) {
    const button = document.querySelector('.fancybox__button--like')
    let userLikes = button.classList.contains('liked')
    let method;
    if (userLikes) {
        method = 'DELETE';
    } else {
        method = 'POST';
    }
    fetch(slide.likeurl, {
        method: method,
        headers: {
            "X-CSRFToken": Cookies.get('csrftoken')
        },
    }).then(response => {
        if (response.status === 404 && userLikes) {
            return {num_likes: numLikes, liked: false}
        }
        return response.json()
    }).then(data => updateLikes(data.num_likes, data.liked)).catch(_ => getLikeStatus(slide));
}

Fancybox.Plugins.Toolbar.defaults.items.numLikes = {
    type: "button",
    class: "fancybox__button--numlikes",
    label: "numLikes",
    html:
        '? likes',
    click: function (e) {
        e.preventDefault();
        toggleLike(this.fancybox.getSlide());
    },
};
Fancybox.Plugins.Toolbar.defaults.items.like = {
    type: "button",
    class: "fancybox__button--like",
    label: "Like",
    html:
        '<i class="fas fa-heart"></i>',
    click: function (e) {
        e.preventDefault();
        toggleLike(this.fancybox.getSlide());
    },
};


Fancybox.bind('[data-fancybox="gallery"]',
    {
        Toolbar: {
            display: [
                { id: "like", position: "center" },
                { id: "numLikes", position: "center" },
                { id: "counter", position: "left" },
                "slideshow",
                "fullscreen",
                "download",
                "thumbs",
                "close",
            ],
        },
        on : {
            load : (fancybox, carousel) => {
                getLikeStatus(fancybox.getSlide());
            }
        }
    }
);
