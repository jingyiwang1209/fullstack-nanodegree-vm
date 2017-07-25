  var container = $('.latestadded');
  var containermore = $('.moreadded');

  // To request the books with the clicks of like
  $(function() {
      $.ajax({
              type: 'GET',
              url: '/getData',
              dataType: 'json',
          })
          .done(function(res) {
              console.log(res['list']);
              result = res['list'];
              for (var i = 0; i < result.length; i++) {
                  createData(result[i], i);
              }
          });

      // Request the clicks of like
      $(document).on('click', '[id^=like]', function() {

          var likeId = $(this).attr('id').split('like')[1];
          var data = {
              'likeId': likeId
          };
          console.log(data);

          $.ajax({
              url: "/like",
              dataType: 'json',
              type: 'POST',
              data: JSON.stringify(data),
              contentType: 'application/json;charset=UTF-8',
          }).
          done(function(response) {
              var clicks = response['clicks'];
              var msg = response['msg'];
              var likedBook = $('#count' + likeId);
              likedBook.text(msg);
              if (clicks == 0) {
                  $('#like' + likeId).css({
                      "background-position": "0 0",
                      "animation": "unfave-heart 1s steps(28,end)"
                  });
              } else {
                  $('#like' + likeId).css({
                      "background-position": "-2800px 0",
                      "animation": "fave-heart 1s steps(28,start)"
                  });
              }
          }).
          fail(function(res) {
              var modal = $(".modal");
              modal.show();

          });

      });

  });

  // helper functions
  function createData(result, index) {
      var li = $('<li>').attr({
          'class': 'bookItem'
      });
      var img = $('<img>').attr({
          'src': result.picture,
          'id': 'picture' + result.id,
          'class': 'bookImage'
      });
      var imgShell = $('<div>').attr('class', 'imgShell');
      imgShell.append(img);

      var name = $('<a>').attr('href', '/books/' + result.id);
      name.css('display', 'block');
      var like = $('<div>').attr({
          'id': 'like' + result.id,
          'class': 'heart'
      });
      var count = $('<div>').attr({
          'id': 'count' + result.id
      });
      count.css({
          'padding-left': '32px',
          'padding-top': '10px'
      });

      count.text(result.like);
      // like.text('heart ');
      if (result.like == 0) {
          like.css({
              "background-position": "0 0",
          });
      } else {
          like.css({
              "background-position": "-2800px 0",
          });
      }

      name.text(result.name);
      var bottomShell = $('<div>').attr('class', 'bottomShell');
      bottomShell.append(name).append(like).append(count);
      bottomShell.css('padding', '15px');

      var quickView = $('<button>').attr({
          'class': 'quickView',
          'id': 'book' + result.id
      });
      quickView.text('Quick View');
      li.append(imgShell).append(bottomShell).append(quickView);
      if (index <= 3) {
          container.append(li);
      } else {
          containermore.append(li);
      }

  }


  function sortData(result) {
      var li = $('<li>').attr({
          'class': 'bookItem'
      });
      var img = $('<img>').attr({
          'src': result.picture,
          'id': 'picture' + result.id,
          'class': 'bookImage'
      });
      var imgShell = $('<div>').attr('class', 'imgShell');
      imgShell.append(img);

      var name = $('<a>').attr('href', '/books/' + result.id);
      name.css('display', 'block');
      var like = $('<div>').attr({
          'id': 'like' + result.id,
          'class': 'heart'
      });
      var count = $('<div>').attr({
          'id': 'count' + result.id
      });
      count.css({
          'padding-left': '32px',
          'padding-top': '10px'
      });

      count.text(result.like);
      // like.text('heart ');
      if (result.like == 0) {
          like.css({
              "background-position": "0 0",
          });
      } else {
          like.css({
              "background-position": "-2800px 0",
          });
      }

      name.text(result.name);
      var bottomShell = $('<div>').attr('class', 'bottomShell');
      bottomShell.append(name).append(like).append(count);
      bottomShell.css('padding', '15px');

      var quickView = $('<button>').attr({
          'class': 'quickView',
          'id': 'book' + result.id
      });
      quickView.text('Quick View');
      li.append(imgShell).append(bottomShell).append(quickView);

      container.append(li);

  }

  // To get the most liked books
  var sort = $('.sort');
  sort.on('click', function() {
      var text = sort.text();
      console.log('text', text);

      $.ajax({
          type: 'GET',
          url: '/getSort',
          dataType: 'json'
      }).
      done(function(res) {
          container.html('');
          containermore.html('');
          $('.mtitle').text('');
          $('.ltitle').html("Popular books<a href='/books'><span class='sort' style='float: right; font-size:1rem;vertical-align:text-bottom;font-weight: normal;padding-top:8px;'>Go back</span></a>");
          result = res['sorted'];
          for (var i = 0; i < result.length; i++) {
              sortData(result[i]);
          }

      });

  });

  $(document).on('click', '[id^=picture]', function() {
      var bookId = $(this).attr('id').split('picture')[1];
      window.location.href = '/books/' + bookId;
  });


  // Present the QuickView

  bookDetails = $('.bookDetails');
  bookDetails.on('click', function() {
      bookDetails.hide();
  });

  $(document).on('click', '[id^=book]', function() {
      bookDetails.show();

      var bookId = $(this).attr('id').split('book')[1];
      var data = {
          'bookId': bookId
      };
      $.ajax({
          url: "/bookDetails",
          type: 'POST',
          dataType: 'json',
          data: JSON.stringify(data),
          contentType: 'application/json;charset=UTF-8',
      }).
      done(function(res) {
          $('.picture').attr("src", res['picture']);
          $('.name').text(res['name']);
          $('.author').text(res['author']);
          $('.link').attr('href', res['link']);
          $('.description').text(res['description']);
          $('.category').text(res['category']);
          var cate = res['category'];
          $('.category').attr("href", "/books/" + cate);
          $('.detail').attr("href", "/books/" + res['bookId']);

      });

  });