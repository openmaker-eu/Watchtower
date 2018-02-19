var cursor = 10;
var isReadyForLoading = true;
var isEventsOver = false;
var topic_id = -1;

var main = function () {
      $("#spin").spinner();
      topic_id = $('#topic_dropdown > li.active > a').attr("data-id");
};
$(document).ready(main);

$(document).ready(function () {

    $("#topic_dropdown").on('click', 'li a', function () {
        topic_id = $(this).attr("data-id");
        isEventsOver = false;
        getEvents();
    });

    $("#location_dropdown").on('click', 'li a', function () {
        $('#all-events').empty();
        $("#spin").show();
        var topic_id = $('#topic_dropdown .active a').attr('data-id');
        var filter = $('.btn-success').val();
        var location = $(this).attr("data-id");
        $.ajax({
            url: '/get_events',
            method: 'GET',
            data: {
                'topic_id':topic_id,
                'filter': filter,
                'location':location
            },
            timeout: 10000,
            error: function () {
                $('#all-events').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#all-events').empty();
                $('#all-events').append(html);
                $("#spin").hide();
            }
        });
    });

    $(window).scroll(function () {
        if ($("#spin").css("display") == "none" && (!isEventsOver) && ($(window).scrollTop() + $(window).height() == $(document).height()) && (isReadyForLoading)) {
            isReadyForLoading = false;
            loadNewEvents();
        }
    });

});



function loadNewEvents() {
    $("#spin").show();
    console.log("load new events");
    filter = $('.btn-success').val();
    $(".loader").css("visibility", "visible");
    $.ajax({
        type: "GET",
        url: "/get_events",
        data: {topic_id: topic_id, filter: filter, cursor: cursor, place: ''},
        success: function (response) {
            console.log("success");
            if (response.length < 200) isEventsOver = true;
            isReadyForLoading = true;
            $(".loader").css("visibility", "hidden");
            cursor += 10;
            $("#all-events").append(response);
            $("#spin").hide();
        },
        error: function (response) {
            console.log("failed");
            $("#spin").hide();
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
        data: {topic_id: topic_id, filter: filter, cursor: cursor, place: ''},
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

function hideEvent(event_link, description, elem) {
    var is_hide = ($(elem).attr("hiddenflag") == 'true');
    is_hide = !is_hide;
    console.log($(elem));

    $.ajax({
        url: '/hide_event',
        method: 'POST',
        data: {
            'event_link': event_link,
            'description':description,
            'is_hide': is_hide
        },
        success: function (html) {
          if (is_hide) {
            $("div[url='" + event_link + "']" ).css("opacity", "0.3");
            $(elem).attr("hiddenflag", true);
            $(elem).html("Unhide")
          }
          else {
            $("div[url='" + event_link + "']" ).css("opacity", "1");
            $(elem).attr("hiddenflag", false);
            $(elem).html("Hide")
          }
        }
    });
}
