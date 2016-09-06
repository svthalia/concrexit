var blocked= false;


$(document).ready(function(){
    $("#collection-div").hide();
    $(".post-slider .slides").trigger("slideTo", boardPositions.indexOf(boardNr));
    $(".bestuur-list").hide();
    $("#board" + boardNr).show();
    $("#title").html(boardTitles[boardNr]);
    window.history.pushState(boardNr, 'Title', '/association/committees/boards/' + boardNr);
});

$("#carousel-prev").click(function(){
    if(blocked) {
        return;
    }
    blocked = true;
    var number = boardPositions.indexOf(boardNr) - 1;
    
    if (number < 0){
        number = parseInt(boardMax) - 1;
    }
    boardNr = boardPositions[number];
    $(".bestuur-list").hide();
    $("#board" + boardNr).show();
    $("#title").html(boardTitles[boardNr]);
    window.history.pushState(boardNr, 'Title', '/association/committees/boards/' + boardNr);
    setTimeout(function(){blocked=false}, 500);
});

$("#carousel-next").click(function(){
    if(blocked) {
        return;
    }
    blocked = true;
    var number = boardPositions.indexOf(boardNr) + 1;
    var maximum = parseInt(boardMax);
    
    if (number >= maximum){
        number = 0;
    }
    
    boardNr = boardPositions[number];
    $(".bestuur-list").hide();
    $("#board" + boardNr).show();
    $("#title").html(boardTitles[boardNr]);
    window.history.pushState(boardNr, 'Title', '/association/committees/boards/' + boardNr);
    setTimeout(function(){blocked=false}, 500);
});

$(document).on('click', '#collectionButton', function(event) {
    if(blocked) {
        return;
    }
    event.preventDefault();
    
    $("#collection-div").css("display", "block");
    $("#boardTitle").html("Alle bestuursjaren");
    $("#bestuurCarousel").hide();
    $("#ledenTitle").hide();
    $(".board-directory").hide();
    window.history.pushState("board", "Title", "/association/committees/boards/");
});
