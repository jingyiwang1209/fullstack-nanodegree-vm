var modal = $(".modal");

$(".login").on('click', function() {
    modal.show();
});
modal.on('click', function(e) {
    modal.hide();
});
var addNew = $('.addNew');

addNew.on('click', function() {
    modal.show();
});

var sendFeedback = $('.sendFeedback');
sendFeedback.on('click', function() {
    modal.show();
});
