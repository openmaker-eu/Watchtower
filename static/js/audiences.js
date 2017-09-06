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
            }
        }).success(function (html) {
            $('#audiencecontainer').empty();
            $('#audiencecontainer').append(html);
            $("#spin").hide();
        });
    });
});
