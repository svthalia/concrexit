function disableSaving(value){
    for (const child of document.getElementsByClassName("submit-row")[0].children) {
        if (value)
            child.setAttribute("disabled","true")
        else
            child.removeAttribute("disabled")
    }
}

const pond = document.querySelector('.filepond--root');
pond.addEventListener("FilePond:initfile", () => {
    disableSaving(true)
});

pond.addEventListener("FilePond:processfiles", () => {
    disableSaving(false)
})
