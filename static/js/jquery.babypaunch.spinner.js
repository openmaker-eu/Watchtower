/*
* 개발: 정대규
* 최초: 2016.11.15
* 수정: 2017.01.04
*/
$.fn.spinner = function(data){
	/*
	* body의 scroll을 제어하기 위해
	* spinner가 show/hide되는 시점에 처리를 위한 이벤트에 callback을 이용한다.
	*/
	$.each(["show", "hide"], function(i, e) {
		var $e = $.fn[e];
		$.fn[e] = function(){
			this.trigger(e);
			return $e.apply(this, arguments);
		};
	});

	//options
	var $spinner = {
		color: "white"
		, background: "rgba(0,0,0,0.5)"
		, html: "hourglass"
		, absolute: true
		, spin: true
	};

	this.init = function($spinner){
		return "<style id='data-spinner-style'>\n"
			+ "body.unselectable {\n"
				+ "\t-webkit-user-select: none;"
				+ "\t-moz-user-select: none;"
				+ "\t-ms-user-select: none;"
				+ "\t-o-user-select: none;"
				+ "\tuser-select: none;\n"
			+ "}\n"
			+ "[data-spinner-layer] {\n"
				+ "\tdisplay: none; position: fixed; top: 0; left: 0;"
				+ "\tbackground: " + $spinner.background + ";"
				+ "\twidth: 100%; height: 100%; padding: 0; margin: 0;\n"
			+ "}\n"
			+ "[data-spinner-bar] {\n"
				+ "\tcolor: " + $spinner.color + ";"
				+ "\tposition: absolute; top: calc(50% - 30px); left: calc(50% - 15px); font-weight: bold; font-size: 40px;"
				+ ($spinner.spin ? "\t-webkit-animation: data-spinner 2s linear infinite; -moz-animation: data-spinner 2s linear infinite; animation: data-spinner 2s linear infinite;\n" : "")
			+ "}\n"
			+ "\t@-moz-keyframes data-spinner {100% {-moz-transform: rotate(360deg); transform: rotate(360deg);}}\n"
			+ "\t@-webkit-keyframes data-spinner {100% {-webkit-transform: rotate(360deg); transform: rotate(360deg);}}\n"
			+ "\t@keyframes data-spinner {100% {-webkit-transform: rotate(360deg); transform: rotate(360deg);}}\n"
		+ "</style>";
	}

	$.extend($spinner, data);
	var $style = this.init($spinner);

	return this.each(function(){
		if($("#data-spinner-style").length === 0){
			$("head").append($style);
		}

		var icon = $spinner.html === "hourglass" ? "&#x29D6;" : ($spinner.html === "spinner" ? "&#x21BB" : $spinner.html);

		$spin = $(this);
		$spin
			.attr({"data-spinner-layer": "", "data-spinner-body": $("body").css("overflow")})
			.html("<div data-spinner-bar>" + icon + "</div>")
			.on("show", function(){
				$("body").css("overflow", "hidden");
			})
			.on("hide", function(){
				$("body").css("overflow", $spinner.absolute ? "" : $spin.attr("data-spinner-body")).removeClass("unselectable");
			})
		;

		$("body").addClass("unselectable");
	});
}
