$(document).ready(function () {
    $("#spin").spinner();
    $(".dropdown-menu").on('click', 'li a', function () {
        $('#audiencecontainer').empty();
        $("#spin").show();
        var aid = $(this).attr("data-id");
        $.ajax({
            url: '/Audience',
            method: 'POST',
            data: {
                'alertid': aid
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
        if ($(window).scrollTop() + $(window).height() == $(document).height()) {
            if ($('#audiencewrapper').length != 0) {
                $("#spin").show();
                var ncursor = $("#audiencewrapper > div").last().attr("cursor");
                var aid = $("#audienceDiv").attr("alertid");
                $.ajax({
                    url: '/Audience/scroll',
                    method: 'POST',
                    data: {
                        'next_cursor': ncursor,
                        'alertid': aid
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
    var aid = $("#audienceDiv").attr("alertid");
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
