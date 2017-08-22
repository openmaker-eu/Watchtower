var lastPostScrollNumber = 0;
var isReadyForLoading = true;
var topic_id = -1;

$(document).ready(function(){
	$('a.feedalerts').click(function() {
		topic_id = $(this).attr("data-id");
    	getConversations($("#day"), "day");
    	lastPostScrollNumber = 0;
    });
	$(window).scroll(function() {
	    if(($(window).scrollTop() + $(window).height() == $(document).height()) && (isReadyForLoading)) {
	    	isReadyForLoading = false;
	        console.log("bottom");
	        loadNewConversations();
    	}
	});
});

function loadNewConversations() {
	var date = $(".btn-success")[0].id;
	$(".loader").css("visibility","visible");
	$.ajax({
	    type: "GET",
	    url: "/Comments",
	    data: { topic_id: topic_id, timeFilter: date, paging: lastPostScrollNumber},
	    success: function (response) {
	        console.log("success");
	    	isReadyForLoading = true;
	        $(".loader").css("visibility","hidden");
	        lastPostScrollNumber += 10;
					 $("#all-comments").append(response);
	        console.log(lastPostScrollNumber);
	        updateReadMores();
	    },
	    error: function (response){
	        console.log("failed");
					 $("#all-comments").empty();
					 $("#all-comments").append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
	    }
	});
}

function getConversations(clickedButton,date) {
	$(".btn-success").removeClass("btn-success");
	$("#all-comments").empty();
	$(clickedButton).addClass("btn-success");
	lastPostScrollNumber = 0;
	$.ajax({
	    type: "GET",
	    url: "/Comments",
	    data: { topic_id: topic_id, timeFilter: date, paging: lastPostScrollNumber},
	    success: function (response) {
				console.log(response);
	        console.log("success");
	        lastPostScrollNumber += 10;
	        $("#all-comments").empty();
					$("#all-comments").append(response);
	        $(".btn-group").css("visibility","visible")
	        updateReadMores();
	    },
	    error: function (response){
	        console.log("failed");
					$("#all-comments").append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
	    }
	});
}

function updateReadMores() {
	var allButtons = document.querySelectorAll("[id^=read-more-post-button]");
	for(var i in allButtons){
		if(allButtons[i].previousElementSibling != null){
		    if(!(allButtons[i].previousElementSibling.offsetHeight < allButtons[i].previousElementSibling.scrollHeight)){
		    	allButtons[i].remove();

		    }
		}
	}
	var allButtons = document.querySelectorAll("[id^=read-more-comment-button]");
	for(var i in allButtons){
		if(allButtons[i].previousElementSibling != null){
		    if(!(allButtons[i].previousElementSibling.offsetHeight < allButtons[i].previousElementSibling.scrollHeight)){
		    	allButtons[i].remove();
		    }
		}
	}
	$(".all-comments-closed").css("display","none");
}

function openInnerComment(param) {
	console.log(param.parentElement.nextElementSibling);
	if(param.textContent == "-") {
		$(param.parentElement.nextElementSibling).css("display","none");
		param.textContent = "+";
	} else {
		$(param.parentElement.nextElementSibling).css("display","inherit");
		param.textContent = "-";
	}
}

function openComment(param) {
	console.log("lol")
	console.log(param.parentElement.parentElement.childNodes);
	if(param.textContent == "-") {
		$(param.parentElement.parentElement.childNodes[7]).css("display","none");
		$(param.parentElement.parentElement.childNodes[7]).removeClass("all-comments-opened");
		$(param.parentElement.parentElement.childNodes[7]).addClass("all-comments-closed");
		param.textContent = "+";
	} else {
		$(param.parentElement.parentElement.childNodes[7]).css("display","inherit");
		$(param.parentElement.parentElement.childNodes[7]).removeClass("all-comments-closed");
		$(param.parentElement.parentElement.childNodes[7]).addClass("all-comments-opened");
		param.textContent = "-";
	}
}

function readMore(param) {
	console.log(param.parentElement.childNodes);
	if(param.textContent == "Read More") {
		$(param.parentElement.childNodes[1]).css("max-height","none");
		param.textContent = "Read Less";
	} else {
		$(param.parentElement.childNodes[1]).css("max-height","4em");
		param.textContent = "Read More";
	}
}

function readMorePost(param) {
	console.log(param.previousElementSibling);
	if(param.textContent == "Read More") {
		$(param.previousElementSibling).css("max-height","none");
		param.textContent = "Read Less";
	} else {
		$(param.previousElementSibling).css("max-height","11.7em");
		param.textContent = "Read More";
	}
}
