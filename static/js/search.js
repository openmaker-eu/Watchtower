$(document).ready(function () {
    $('#searchButton').click(function (e) {
        $("#spin").spinner();
        $('#newscontainer').empty();
        $("#spin").show();
        var keys = $("#keywords").val();
        var domains = $("#domains").val();
        var cities = $("#cities").val();
        var countries = $("#countries").val();
        var langs;
        if ($("#languages").val() === null) {
            langs = "";
        } else {
            langs = $("#languages").val().join();
        }
        var mention_location = $("#mention_location").val();
        var mention_language;
        if ($("#mention_language").val() === null) {
            mention_language = "";
        } else {
            mention_language = $("#mention_language").val().join();
        }
        var ncursor;
        if ($("ol > div").last().attr("cursor") === undefined) {
            ncursor = 0;
        } else {
            ncursor = $("ol > div").last().attr("cursor");
        }


        $.ajax({
            url: '/get_news',
            method: 'GET',
            data: {
                'keywords': keys,
                'domains': domains,
                'languages': langs,
                'cities': cities,
                'countries': countries,
                'mention_language': mention_language,
                'mention_location': mention_location,
                'cursor': ncursor
            },
            timeout: 10000,
            error: function () {
                $('#newscontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            }
        }).success(function (html) {
            $('#newscontainer').append(html);
            $("#spin").hide();
        });
    });
});

$(document).ready(function () {
    $(window).scroll(function () {
        if ($(window).scrollTop() + $(window).height() == $(document).height()) {
            $("#spin").show();
            var keys = $("#keywords").val();
            var domains = $("#domains").val();
            var cities = $("#cities").val();
            var countries = $("#countries").val();
            var langs;
            if ($("#languages").val() === null) {
                langs = "";
            } else {
                langs = $("#languages").val().join();
            }
            var mention_location = $("#mention_location").val();
            var mention_language;
            if ($("#mention_language").val() === null) {
                mention_language = "";
            } else {
                mention_language = $("#mention_language").val().join();
            }
            var ncursor;
            if ($("ol > div").last().attr("cursor") === undefined) {
                ncursor = -1;
            } else {
                ncursor = $("ol > div").last().attr("cursor");
            }

            if (ncursor != 0) {
                $.ajax({
                    url: '/get_news/scroll',
                    method: 'GET',
                    data: {
                        'keywords': keys,
                        'domains': domains,
                        'languages': langs,
                        'cities': cities,
                        'countries': countries,
                        'mention_language': mention_language,
                        'mention_location': mention_location,
                        'cursor': ncursor
                    },
                    timeout: 10000,
                    error: function () {
                        $('#newscontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                        $("#spin").hide();
                    }
                }).success(function (html) {
                    $('#news').append(html);
                    $("#spin").hide();
                });
            } else {
                $("#spin").hide();
            }
        }
    });
});
