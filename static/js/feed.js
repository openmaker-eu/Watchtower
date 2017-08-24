$(document).ready(function () {
    if ($('#feedDiv').length != 0) {
        $("#spin").spinner();
        $('#spin').show();
        var interval = setInterval(function () { // this code is executed every 500 milliseconds:
            if ($('blockquote').length === $('.twitter-tweet-error').length) {
                clearInterval(interval);
                $('.twitter-tweet-error').remove()
                $('#spin').hide();
            }

        }, 500);
    }
});


$(document).ready(function () {
  $(".dropdown-menu").on('click', 'li a', function () {
    var selText = $(this).children("h4").html();
    $(this).parent('li').siblings().removeClass('active');
    $(this).parents('.btn-group').find('.selection').html(selText);
    $(this).parents('li').addClass("active");
  });
    $(window).scroll(function () {
        if ($(window).scrollTop() + $(window).height() == $(document).height()) {
            if ($('#feedDiv').length != 0) {
                $("#spin").show();
                var tid = $("ol > div").last().attr("tweetid");
                var aid = $("ol").attr("alertid");
                $.ajax({
                    url: '/Feed/scroll',
                    method: 'POST',
                    data: {
                        'lastTweetId': tid,
                        'alertid': aid
                    }
                }).success(function (html) {
                    $('#tweets').append(html);
                    var interval = setInterval(function () { // this code is executed every 500 milliseconds:
                        if ($('blockquote').length === $('.twitter-tweet-error').length) {
                            clearInterval(interval);
                            $('.twitter-tweet-error').remove()
                            $('#spin').hide();
                        }

                    }, 500);
                });
            }
        }
    });
});

$(document).ready(function () {
    $("#spin").spinner();
    $('a.feedalerts').click(function () {
        $('#feedcontainer').empty();
        $("#spin").show();
        var aid = $(this).attr("data-id");
        $.ajax({
            url: '/Feed',
            method: 'POST',
            data: {
                'alertid': aid
            },
            timeout: 10000,
            error: function () {
                $('#feedcontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            }
        }).success(function (html) {
            $('#feedcontainer').empty();
            $('#feedcontainer').append(html);
            var interval = setInterval(function () { // this code is executed every 500 milliseconds:
                console.log("I'm waiting");
                if ($('blockquote').length === $('.twitter-tweet-error').length) {
                    clearInterval(interval);
                    $('.twitter-tweet-error').remove()
                    $('#spin').hide();
                }

            }, 500);
        });
    });
});

$(document).ready(function () {
    if ($('#feedDiv').length != 0) {
        setInterval(function () {
            var tid = $("ol > div").first().attr("tweetid") || -1;
            var aid = $("ol").attr("alertid");
            $.ajax({
                url: '/newTweets',
                method: 'POST',
                data: {
                    'alertid': aid,
                    'tweetid': tid
                }
            }).success(function (response) {
                response = parseInt(response);
                console.log(response);
                if (response > 0) {
                    $('#newTweetsButton').remove();
                    var html = "<button type='button' onclick='refreshTweets();' id='newTweetsButton' style='width: 100%' class='btn btn-primary'>" + response + " new tweets</button>";
                    $('#tweets').prepend(html);
                }
            });
        }, 10000);
    }
});

function refreshTweets() {
    $('#spin').show();
    var tid = $("ol > div").first().attr("tweetid") || -1;
    var aid = $("ol").attr("alertid");
    $.ajax({
        url: '/newTweets/get',
        method: 'POST',
        data: {
            'alertid': aid,
            'tweetid': tid
        }
    }).success(function (html) {
        $('#newTweetsButton').remove();
        $('p').remove();
        $('#tweets').prepend(html);
        var interval = setInterval(function () { // this code is executed every 500 milliseconds:
            console.log("I'm waiting");
            if ($('blockquote').length === $('.twitter-tweet-error').length) {
                clearInterval(interval);
                $('.twitter-tweet-error').remove()
                $('#spin').hide();
            }

        }, 500);
    });
}
