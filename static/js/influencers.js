$(document).ready(function () {
    $("#spin").spinner();
    $(".dropdown-menu").on('click', 'li a', function () {
        $('#influencers').empty();
        $("#spin").show();
        var filter = $('.btn-success').val();

        $.ajax({
            url: '/Influencers',
            method: 'POST',
            timeout: 10000,
            error: function () {
                $('#influencerscontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#influencerscontainer').empty();
                $('#influencerscontainer').append(html);
                $("#spin").hide();
            }
        });
    });

    $("#location_dropdown").on('click', 'li a', function () {
        $('#influencers').empty();
        $("#spin").show();
        var filter = $('.btn-success').val();
        var location = $(this).attr("data-id");
        $.ajax({
            url: '/Influencers',
            method: 'POST',
            data: {'location': location},
            timeout: 10000,
            error: function () {
                $('#influencers').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#influencers').empty();
                $('#influencers').append(html);
                $("#spin").hide();
            }
        });
    });

    $(window).scroll(function () {
      if ($("#spin").css("display") == "none" && $(window).scrollTop() + $(window).height() == $(document).height()) {
          var ncursor = 0;
          var filter = $('.btn-success').val();
          if($("#influencers > div").last().attr("cursor") != undefined) ncursor = $("#influencers > div").last().attr("cursor");
          if (ncursor != 0 && $('#influencers').length != 0) {
                $("#spin").show();
                var topic_id = $("#influencers").attr("topicID");
                $.ajax({
                    url: '/Influencers/scroll',
                    method: 'POST',
                    data: {
                        'next_cursor': ncursor,
                        'filter':filter

                    },
                    success: function (html) {
                        $('#influencers').append(html);
                        $("#spin").hide();
                    }
                });
            }
        }
    });
});

function hideInfluencer(influencer_id, description, elem) {
    var is_hide = ($(elem).attr("hiddenflag") === 'true');
    is_hide = !is_hide;

    $.ajax({
        url: '/hide_influencer',
        method: 'POST',
        data: {
            'influencer_id': influencer_id,
            'description':description,
            'is_hide': is_hide
        },
        success: function (html) {
          if (is_hide) {
            $("#".concat(influencer_id)).css("opacity", "0.3");
            $(elem).attr("hiddenflag", true);
            $(elem).html("Unhide")
          }
          else {
            $("#".concat(influencer_id)).css("opacity", "1");
            $(elem).attr("hiddenflag", false);
            $(elem).html("Hide")
          }
        }
    });
}

function fetchFollowers(influencer_id, elem) {
        var fetching = ($(elem).attr("fetchflag") === 'true');
        fetching = !fetching;
        console.log(influencer_id);

        $.ajax({
        url: '/fetch_followers',
        method: 'POST',
        data: {
            'influencer_id': influencer_id,
            'fetching': fetching
        },
        success: function (html) {
          if (fetching) {
            $("#".concat(influencer_id)).css("background-color", 'grey');
            $(elem).attr("fetchflag", true);
            $(elem).html("Cancel fetch followers")
          }
          else {
            $("#".concat(influencer_id)).css("background-color", "white");
            $(elem).attr("fetchflag", false);
            $(elem).html("Fetch followers")
          }
        }

    });
}
