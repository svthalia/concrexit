function startTimer(enddate_string, display) {
    var end_seconds = (new Date(enddate_string)).getTime()/1000;
    var now_seconds = (new Date()).getTime()/1000;
    var distance = end_seconds - now_seconds;

    var minutes = Math.floor(distance/60);
    var seconds = Math.floor(distance%60);

    updateText(minutes, seconds, display);

    timer = setInterval(function () {
        if (minutes*60 + seconds <=0) {
            clearInterval(timer);
            timer = null;
            location.reload(true);
        }
        else
        {
            if(seconds == 0){
                seconds = 59;
                minutes--;
            }
            else
                seconds--;

            updateText(minutes, seconds, display);
        }
    }, 1000);
}

function updateText(minutes, seconds, display)
{
    display.textContent = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
}
