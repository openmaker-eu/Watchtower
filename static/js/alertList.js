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
