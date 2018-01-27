$(document).ready(function () {
    $("#topic_dropdown").on('click', 'li a', function () {
        var selText = $(this).children("h4").html();
        $(this).parent('li').siblings().removeClass('active');
        $(this).parents('.btn-group').find('.selection').html(selText);
        $(this).parents('li').addClass("active");
    });
    $("#spin").spinner();
    $("#topic_dropdown").on('click', 'li a', function () {
        $("#spin").show();
        $.ajax({
            url: '/Tweets',
            method: 'GET',
            data: {
              'change': 1
            },
            timeout: 10000,
            success: function (html) {
                $('#tweetscontainer').empty();
                $('#tweetscontainer').append(html);
                $("#spin").hide();
            }
        });
    });
});

function saveTweet(tweet_id) {
    var text = $('#tweet_'.concat(tweet_id)).find("#description").text();
    var date = $('#tweet_'.concat(tweet_id)).find("#date").val();
    var items = getParameters();
    var news_id = -1;
    if(Object.keys(items).length > 0 && items.news_id){
        news_id = items.news_id;
    }
    $.ajax({
        url: "/Tweets",
        method: 'POST',
        data: {
            'tweet_id': tweet_id,
            'posttype': 'update',
            'text': text,
            'date': date,
            'news_id': news_id
        }
    }).success(function (response) {
        $('#tweet_'.concat(tweet_id)).find('.btn-save').attr("disabled", true);;
        swal("Good job!", "Your tweet is saved!", "success")
    });
}

function removeTweet(tweet_id) {
  swal({
    title: "Are you sure?",
    text: "Your will not be able to recover this tweet!",
    type: "warning",
    showCancelButton: true,
    confirmButtonClass: "btn-danger",
    confirmButtonText: "Yes, delete it!",
    closeOnConfirm: false
    },
    function(){
      $.ajax({
          url: "/Tweets",
          method: 'POST',
          data: {
              'tweet_id': tweet_id,
              'posttype': 'remove'
          }
      }).success(function (response) {
          $('#tweet_'.concat(tweet_id)).remove();
      });
      swal("Deleted!", "Your imaginary file has been deleted.", "success");
    });
}
