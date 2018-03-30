$(document).ready(function () {
    $('.has-spinner').click(function (e) {
        update();
    });
});

function update() {


    var twitterPin = $("#form-twitter-pin").val();

    $(this).toggleClass('active');
    $.ajax({
        url: '/twitter_auth',
        method: 'POST',
        data: {
            'twitter_pin': twitterPin
        },
        timeout: 10000,
        error: function () {
            alert("Please, try again later.");
        }
    }).success(function (response) {
        $(".has-spinner").toggleClass('active');
        if (response.response) {
            swal({
                    title: "Twitter Auth",
                    text: "Your token is added/updated!",
                    type: "success",
                    showCancelButton: false,
                    confirmButtonClass: "btn-success",
                    confirmButtonText: "Go to Topics",
                    closeOnConfirm: false
                },
                function () {
                    location.href = response.redirectUrl;
                });
        }
    });
}
