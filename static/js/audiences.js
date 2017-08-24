
$(document).ready(function () {
  $(".dropdown-menu").on('click', 'li a', function () {
    var selText = $(this).children("h4").html();
    $(this).parent('li').siblings().removeClass('active');
    $(this).parents('.btn-group').find('.selection').html(selText);
    $(this).parents('li').addClass("active");
  });
    $("#spin").spinner();
    $('a.audiencealerts').click(function () {
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
