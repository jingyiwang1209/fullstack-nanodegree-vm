var stars = $('.stars span');
var point = $('.point');


// helper function
function handleStar() {
    $(this).prevAll().addBack().css('color', '#ff0');
}

$(function() {
    for (var i = 0; i < stars.length; i++) {
        $(stars[i]).attr('data-count', i);
        $(stars[i]).on('mouseenter', handleStar);

        $(stars[i]).on('click', function() {
            $(this).data('clicked', true);
            var count = parseInt($(this).attr('data-count'));
            point.text(count + 1);

            handleStar;
        });

        $(stars[i]).on('mouseleave', function() {
            for (var j = 0; j < stars.length; j++) {
                if ($(this).data('clicked') != true) {
                    $(stars[j]).css('color', '#fff');
                }
            }
        });
    }
});

$('.sendFeedback').on('click', function() {
    var points = point.text();
    var feedback = $('.feedback').val();
    if (points === '') {
        $('.result').text('Please do rating.');
        return;
    }

    if (feedback === '')  {
        $('.result').text('Please write your feedback.');
        return;
    }

    var bookid = $('.feedback').attr('id').split('for')[1];
    var data = {
        'points': points,
        'feedback': feedback,
        'bookid': bookid
    };
    $.ajax({
            type: 'POST',
            url: "/ratings",
            dataType: 'json',
            data: JSON.stringify(data),
            contentType: 'application/json;charset=UTF-8',
        })
        .done(function(res) {

            // {'bookid':bookid,'feedback':feedback,
            //      'reader':username,'points':points}

            var reader = $('<span>').attr('class', 'reader');
            var readerStars = $('<span>').attr('class', 'readerStars');
            var readerContents = $('<div>').attr('class', 'readerContents');

            reader.text(res['reader']);
            readerContents.text(res['feedback']);
            for (var i = 0; i < res['points']; i++) {
                readerStars.append('<i class="fa fa-star" aria-hidden="true">');
            }

            $('.feedbacks').prepend(readerContents).prepend(readerStars).prepend(reader);

        });
});