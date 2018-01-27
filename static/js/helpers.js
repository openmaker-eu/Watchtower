String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

function getParameters(){
  var queryDict = {};
  location.search.substr(1).split("&").forEach(function(item) {
    if(item.split("=")[0] !== ""){
        queryDict[item.split("=")[0]] = item.split("=")[1];
    }
  });
  return queryDict;
}
