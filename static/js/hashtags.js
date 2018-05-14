$(document).ready(function () {
    $("#topic_dropdown").on('click', 'li a', function () {
        var selText = $(this).children("h4").html();
        $(this).parent('li').siblings().removeClass('active');
        $(this).parents('.btn-group').find('.selection').html(selText);
        $(this).parents('li').addClass("active");
    });
});

$(document).ready(function () {
    $("#spin").spinner();
    $("#topic_dropdown").on('click', 'li a', function () {
        $("#spin").show();
        $.ajax({
            url: '/Hashtags',
            method: 'POST',
            data: {},
            timeout: 10000,
            error: function () {
                $('#hashtags').empty();
                $('#hashtags').append("There is no hashtag information!");
                $("#spin").hide();
            },
            success: function (html) {
                $('#hashtags').empty();
                $('#hashtags').append(html);
                $("#spin").hide();
            }
        });
    });
});
