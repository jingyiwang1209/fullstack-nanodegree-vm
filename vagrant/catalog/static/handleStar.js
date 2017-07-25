var number = $('.averPoints').text();
var starList = $('.starList');
if (Math.round(number) > number) {
    for (var i = 0; i < number - 1; i++) {
        starList.append('<i class="fa fa-star" aria-hidden="true">');
    }
    var halfStar = '<i class="fa fa-star-half-o" aria-hidden="true"></i>';
    starList.append(halfStar);
} else {
    for (var i = 0; i < number; i++) {
        starList.append('<i class="fa fa-star" aria-hidden="true">');
    }
}

var bookid = $('.feedback').attr('id').split('for')[1];
var data = {
    'bookid': bookid
};
$(function() {
    $.ajax({
            type: 'POST',
            url: "/getRating",
            dataType: 'json',
            data: JSON.stringify(data),
            contentType: 'application/json;charset=UTF-8',

        })

        .done(function(res) {
            var ratingList = res['ratingList'];
            console.log(ratingList);
            // dic={'star':r.star,'bookid':r.book_id,'userid':r.user_id,
            //    'feedback':r.feedback}

            // <span class='reader'></span><span class='readerStars' style='color:#ff0'></span>
            // <div class='readerContents'></div>
            var feedbacks = $('.feedbacks');

            for (var i = 0; i < ratingList.length; i++) {
                var reader = $('<span>').attr('class', 'reader');
                var readerStars = $('<span>').attr('class', 'readerStars');
                var readerContents = $('<div>').attr('class', 'readerContents');
                readerContents.text(ratingList[i].feedback);
                for (var j = 0; j < ratingList[i].star; j++) {
                    readerStars.append('<i class="fa fa-star" aria-hidden="true">');
                }
                reader.text(ratingList[i].username);
                feedbacks.append(reader).append(readerStars).append(readerContents);
            }

        });

});