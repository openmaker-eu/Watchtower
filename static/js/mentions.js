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
        var topicId = $(this).attr("data-id");
        $.ajax({
            url: '/Mentions',
            method: 'POST',
            data: {
                topic_id: topicId
            },
            timeout: 10000,
            error: function () {
                $('#mentions').empty();
                $('#mentions').append("There is no mention information!");
                $("#spin").hide();
            },
            success: function (html) {
                $('#mentions').empty();
                $('#mentions').append(html);
                $("#spin").hide();
            }
        });
    });
});
