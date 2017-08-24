var main = function () {
    $(".keyword > .bootstrap-tagsinput").on('DOMSubtreeModified', function () {
        var keywordCount = $(".keyword > .bootstrap-tagsinput > .tag").length;
        var limitLeft = 10 - keywordCount;
        if (limitLeft <= 0) {
            $('.counter').css('color', 'red');
            $(".keyword > .bootstrap-tagsinput > input").prop('disabled', true);
            $('.counter').text("Your keyword limit is full. In order to add a new keyword, please remove old ones.");
        } else {
            $('.counter').css('color', 'black');
            $('.counter').text("Keyword Limit: " + limitLeft);
            $(".keyword > .bootstrap-tagsinput > input").prop('disabled', false);
        }
    });
};
$(document).ready(main);

$(document).ready(function () {
    $('#findpages').click(function (e) {
        $('.alert-form').find('input[name="keywords"]').each(function () {
            if ($(this).val() == "" || $(this).val() == null) {
                e.preventDefault();
                $(".keyword > .bootstrap-tagsinput").addClass("input-error");
            }
            else {
                $(this).removeClass('input-error');
            }
        });
        if ($('.input-error').length == 0) {
            $("#spin").spinner();
            $('#pages').empty();
            $("#spin").show();
            var keys = $("#keywords").val();
            $.ajax({
                url: '/getPages',
                method: 'GET',
                data: {
                    'keywords': keys,
                },
                timeout: 10000,
                error: function () {
                    $('#pages').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                    $("#spin").hide();
                }
            }).success(function (html) {
                $('#pages').append(html);
                $("#spin").hide();
            });
        }
    });
});

$(document).ready(function () {
    $('#previewbutton').click(function (e) {
        $('.alert-form').find('input[name="alertname"], input[name="description"], input[name="keywords"], select[name="languages"]').each(function () {
            if ($(this).val() == "" || $(this).val() == null) {
                e.preventDefault();
                if ($(this).attr("name") == "keywords") {
                    $(".keyword > .bootstrap-tagsinput").addClass("input-error");
                }
                else {
                    $(this).addClass('input-error');
                }
            }
            else {
                $(this).removeClass('input-error');
            }
        });
        if ($('.input-error').length == 0) {
            $("#spin").spinner();
            $('#preview').empty();
            $("#spin").show();
            var keys = $("#keywords").val();
            var exkeys = $("#excludedkeywords").val();
            var langs = $("#languages").val().join();
            $.ajax({
                url: '/preview',
                method: 'POST',
                data: {
                    'keywords': keys,
                    'languages': langs,
                    'excludedkeywords': exkeys
                },
                timeout: 10000,
                error: function () {
                    $('#preview').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                    $("#spin").hide();
                }
            }).success(function (html) {
                $('#preview').append(html);
                var interval = setInterval(function () { // this code is executed every 500 milliseconds:
                    console.log("I'm waiting");
                    if ($('blockquote').length === 0) {
                        clearInterval(interval);
                        $('.twitter-tweet-error').remove()
                        $('#spin').hide();
                    }

                }, 500);
            });
        }
    });
});

jQuery(document).ready(function () {
    $('.alert-form  input[name="alertname"], .alert-form  input[name="description"], .alert-form  select[name="languages"]').on('focus', function () {
        $(this).removeClass('input-error');
    });
    $(".keyword > .bootstrap-tagsinput").on('DOMSubtreeModified', function () {
        $(this).removeClass('input-error');
    });

    $('.alert-form').on('submit', function (e) {

        $(this).find('input[name="alertname"], input[name="description"], input[name="keywords"], select[name="languages"]').each(function () {
            if ($(this).val() == "" || $(this).val() == null) {
                e.preventDefault();
                if ($(this).attr("name") == "keywords") {
                    $(".bootstrap-tagsinput").addClass("input-error")
                }
                else {
                    $(this).addClass('input-error');
                }
            }
            else {
                $(this).removeClass('input-error');
            }
        });

    });

});
