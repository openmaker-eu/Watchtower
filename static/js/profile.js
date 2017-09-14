  $(document).ready(function() {
    $('.has-spinner').click(function(e) {
      update();
    });

    $('#form-password').keypress(function(event) {
      if (event.keyCode == 13 || event.which == 13) {
        $('#form-repassword').focus();
        event.preventDefault();
      }
    });

    $('#form-repassword').keypress(function(event) {
      if (event.keyCode == 13 || event.which == 13) {
        $('#form-country').focus();
        event.preventDefault();
      }
    });

    $('#form-country').keypress(function(event) {
      if (event.keyCode == 13 || event.which == 13) {
        update();
      }
    });

  });

  function update() {
    $('.update-form input[type="text"], .update-form input[type="password"], .update-form textarea').on('focus', function() {
      $(this).removeClass('input-error');
    });

    $(".update-form").find('input[type="text"], input[type="password"], textarea').each(function() {
      if ($(this).val() == "") {
        $(this).addClass('input-error');
      } else {
        $(this).removeClass('input-error');
      }
    });

    if ($('.input-error').length == 0) {
      if ($("#form-password").parent().next(".validation").length != 0) // only add if not added
      {
        $("#form-password").parent().next(".validation").remove();
      }
      if ($("#form-repassword").parent().next(".validation").length != 0) // only add if not added
      {
        $("#form-repassword").parent().next(".validation").remove();
      }

      var password = $("#form-password").val();
      var repassword = $("#form-repassword").val();
      var country = $("#form-country").val();

      if (password != repassword && $("#form-repassword").parent().next(".validation").length == 0) // only add if not added
      {
        $("#form-repassword").parent().after("<div class='validation' style='color:red;margin-top: -10px;margin-bottom:10px;'>Please, same password.</div>");

      } else {
        $(this).toggleClass('active');
        $.ajax({
          url: '/profile',
          method: 'POST',
          data: {
            'password': password,
            'country': country
          },
          timeout: 10000,
          error: function() {
            alert("Please, try again later.");
          }
        }).success(function(response) {
          $(".has-spinner").toggleClass('active');
          if (response.response) {
            location.href = response.redirectUrl;
          }
          var returnedData = JSON.parse(response);
          var str = "<div class='validation' style='color:red;margin-top: -10px;margin-bottom:10px;'>".concat(returnedData.message.concat("</div>"));
          if (returnedData.error_type == 1) {
            if ($("#form-country").parent().next(".validation").length == 0) // only add if not added
            {
              $("#form-country").parent().after(str);

            }
          }
        });
      }
    }
  }
