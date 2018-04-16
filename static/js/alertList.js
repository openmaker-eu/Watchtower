$(document).ready(function () {
    var path = window.location.pathname;
    var pathList = path.split("/");
    if (pathList.length === 3) {
        notification(pathList[2]);
    }

});

function notification(alertid) {
    setTimeout('', 10000);
    console.log(alertid);
    $.ajax({
        url: "/message",
        method: 'POST',
        data: {
            'alertid': alertid,
        }
    }).success(function (response) {
        var results = response.split(";");
        var message = results[0];
        var messagetype = results[1];
        if (message != "") {
            $.notify({
                    message: message
                },
                {
                    type: messagetype
                })
        }
        console.log("message:" + message);
    });
}

function alertbuttonclick(aid, ptype) {
    //var aid = $(this).attr("alertid");
    //var ptype = $(this).attr("posttype");
    console.log(ptype);
    $.ajax({
        url: "/Topics",
        method: 'POST',
        data: {
            'alertid': aid,
            'posttype': ptype
        }
    }).success(function (response) {
        $('#alerts').remove();
        $("#alertspage").append(response.topic_list);
        $('#alert_dropdown_menu').empty();
        $("#alert_dropdown_menu").append(response.dropdown_list);
        //console.log("notification :" + aid);
        //notification(aid);
    });
}

function hashtagSave(topic_id, hashtag, isActive) {
    $.ajax({
        url: "/hashtag",
        method: 'POST',
        data: {
            'topic_id': topic_id,
            'hashtag': hashtag,
            'save_type': isActive
        }
    }).success(function (response) {
        if (isActive) {
            $("#{0}_{1}".format(topic_id, hashtag)).removeClass('btn-outline');
        } else {
            $("#{0}_{1}".format(topic_id, hashtag)).addClass('btn-outline');
        }
        $("#{0}_{1}".format(topic_id, hashtag)).attr('onclick', "hashtagSave('{0}', '{1}', {2})".format(topic_id, hashtag, !isActive));
    });
}