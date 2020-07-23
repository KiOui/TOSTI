$(window).click(function() {
    if ($('#footer-menu').hasClass('show') && $('#footer-toggler:visible').length > 0) {
        $('#footer-toggler').click();
    }
});

$('#footer-container').click(function(event){
    if ($('#footer-menu').hasClass('show') &&
        !($(event.target).parents('#footer-toggler').length > 0 || event.target.id === "footer-toggler") &&
        !($(event.target).parents('#overview-button').length > 0 || event.target.id === "overview-button")) {
        console.log("Stopped");
        console.log(event.target);
        console.log(event.target.id);
        console.log(event.target.id === "overview-button");
        event.stopPropagation();
    }
});