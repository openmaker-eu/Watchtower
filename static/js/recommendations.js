$(document).ready(function () {
    $("#spin").spinner();
    $(".dropdown-menu").on('click', 'li a', function () {
        $('#recommendations').empty();
        $("#spin").show();
        var filter = $('.btn-success').val();

        $.ajax({
            url: '/Recommendations',
            method: 'POST',
            data: {
                'filter':filter
            },
            timeout: 10000,
            error: function () {
                $('#recommendations').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#recommendations').empty();
                $('#recommendations').append(html);
                $("#spin").hide();
            }
        });
    });

    $("#location_dropdown").on('click', 'li a', function () {
        $('#recommendations').empty();
        $("#spin").show();
        var filter = $('.btn-success').val();
        $.ajax({
            url: '/Recommendations',
            method: 'POST',
            data: {
                'filter': filter
            },
            timeout: 10000,
            error: function () {
                $('#recommendations').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#recommendations').empty();
                $('#recommendations').append(html);
                $("#spin").hide();
            }
        });
    });

    $(window).scroll(function () {
      if ($("#spin").css("display") == "none" && $(window).scrollTop() + $(window).height() == $(document).height()) {
          var ncursor = 0;
          var filter = $('.btn-success').val();
          if($("#recommendations > div").last().attr("cursor") != undefined) ncursor = $("#recommendations > div").last().attr("cursor");
          if (ncursor != 0 && $('#recommendations').length != 0) {
                $("#spin").show();
                var topic_id = $("#recommendations").attr("topicID");
                $.ajax({
                    url: '/Recommendations/scroll',
                    method: 'POST',
                    data: {
                        'next_cursor': ncursor,
                        'filter':filter

                    },
                    success: function (html) {
                        $('#recommendations').append(html);
                        $("#spin").hide();
                    }
                });
            }
        }
    });
});

function getRecommendedAudience() {
    var topic_id = $("#recommendations").attr("topicID");

    console.log("get rated audience");
    var cursor = 0;
    var filter = $('.btn-success').val();
    $.ajax({
        type: "POST",
        url: "/Recommendations",
        data: {topic_id: topic_id, filter: filter},
        success: function (response) {
            console.log("success");
            cursor += 10;
            $("#recommendations").empty();
            $("#recommendations").append(response);
            $(".btn-group").css("visibility", "visible")
        },
        error: function (response) {
            console.log("failed");
        }
    });
}


function rateAudience(audience_id) {
    var aid = $("#recommendations").attr("topicID");
    var rating = $("#rate_".concat(audience_id)).val();
    if(rating == "") rating = 0;
    $.ajax({
        url: '/rate_audience',
        method: 'POST',
        data: {
            'alertid': aid,
            'rating': rating,
            'audience_id': audience_id
        },
        success: function (html) {
        }
    });
}

function changeFilter(clickedFilter) {
    isEventsOver = false;
    $('.btn-success').removeClass('btn-success').addClass('btn-default');
    $(clickedFilter).removeClass('btn-default').addClass('btn-success');
    getRecommendedAudience();
}
