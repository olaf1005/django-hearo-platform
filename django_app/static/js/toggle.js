$(function(){
    $('.trigger').click(function(e){
        e.preventDefault();
        $( $(this).data('target') ).addClass('active');
    });

    $('.close').click(function(e){
        e.preventDefault();
        $(this).closest('.active').removeClass('active');
    });
});