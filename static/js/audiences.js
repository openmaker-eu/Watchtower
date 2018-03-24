$(document).ready(function () {
    $("#spin").spinner();
    $("#topic_dropdown").on('click', 'li a', function () {
        $('#audiencecontainer').empty();
        $("#spin").show();
        var topicId = $(this).attr("data-id");
        $.ajax({
            url: '/Audience',
            method: 'POST',
            data: {
                'topic_id': topicId
            },
            timeout: 10000,
            error: function () {
                $('#audiencecontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#audiencecontainer').empty();
                $('#audiencecontainer').append(html);
                $("#spin").hide();
            }
        });
    });

    $("#location_dropdown").on('click', 'li a', function () {
        $('#audiencecontainer').empty();
        $("#spin").show();
        // var topicId = $('#topic_dropdown .active a').attr('data-id');
        var location = $(this).attr("data-id");
        $.ajax({
            url: '/Audience',
            method: 'POST',
            data: {
                'location':location
            },
            timeout: 10000,
            error: function () {
                $('#audiencecontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#audiencecontainer').empty();
                $('#audiencecontainer').append(html);
                $("#spin").hide();
            }
        });
    });

    $(window).scroll(function () {
      if ($("#spin").css("display") == "none" && $(window).scrollTop() + $(window).height() == $(document).height()) {
          var ncursor = 0;
          if($("#audiencewrapper > div").last().attr("cursor") != undefined) ncursor = $("#audiencewrapper > div").last().attr("cursor");
          if (ncursor != 0 && $('#audiencewrapper').length != 0) {
                $("#spin").show();
                var topic_id = $("#audienceDiv").attr("alertid");
                $.ajax({
                    url: '/Audience/scroll',
                    method: 'POST',
                    data: {
                        'next_cursor': ncursor
                    },
                    success: function (html) {
                        $('#audiencewrapper').append(html);
                        $("#spin").hide();
                    }
                });
            }
        }
    });
});

function rateAudience(audience_id) {
    var topicId = $("#audienceDiv").attr("alertid");
    var rating = $("#rate_".concat(audience_id)).val();
    if(rating == "") rating = 0;
    $.ajax({
        url: '/rate_audience',
        method: 'POST',
        data: {
            'topic_id': topicId,
            'rating': rating,
            'audience_id': audience_id
        },
        success: function (html) {
        }
    });
}
