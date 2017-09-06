var cursor = 0;
var isReadyForLoading = true;
var isEventsOver = false;
var topic_id = -1;

$(document).ready(function () {

    $(".dropdown-menu").on('click', 'li a', function () {
        topic_id = $(this).attr("data-id");
        isEventsOver = false;
        getEvents();
    });

    $(window).scroll(function () {
        if ((!isEventsOver) && ($(window).scrollTop() + $(window).height() == $(document).height()) && (isReadyForLoading)) {
            isReadyForLoading = false;
            loadNewEvents();
        }
    });

});

function loadNewEvents() {
    console.log("lead new events");
    filter = $('.btn-success').val();
    $(".loader").css("visibility", "visible");
    $.ajax({
        type: "GET",
        url: "/get_events",
        data: {topic_id: topic_id, filter: filter, cursor: cursor},
        success: function (response) {
            console.log("success");
            if (response.length < 200) isEventsOver = true;
            isReadyForLoading = true;
            $(".loader").css("visibility", "hidden");
            cursor += 10;
            $("#all-events").append(response);
        },
        error: function (response) {
            console.log("failed");
        }
    });
}

function getEvents() {
    console.log("get new events");
    cursor = 0;
    filter = $('.btn-success').val();
    $.ajax({
        type: "GET",
        url: "/get_events",
        data: {topic_id: topic_id, filter: filter, cursor: cursor},
        success: function (response) {
            console.log("success");
            if (response.length < 200) isEventsOver = true;
            cursor += 10;
            $("#all-events").empty();
            $("#all-events").append(response);
            $(".btn-group").css("visibility", "visible")
        },
        error: function (response) {
            console.log("failed");
        }
    });
}


function changeFilter(clickedFilter) {
    isEventsOver = false;
    $('.btn-success').removeClass('btn-success').addClass('btn-default');
    $(clickedFilter).removeClass('btn-default').addClass('btn-success');
    getEvents();
}
