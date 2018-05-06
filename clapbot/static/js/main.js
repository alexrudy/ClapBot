$(document).ready(function(){
    $('.datatables').each(function(){
        var table = $(this).dataTable({
            paging: false,
            autoWidth: true,
            ordering: false,
            });
        });
    $('.listing-form').each(function(){
        var id = $(this).attr('data-listing-id')
        $(this).find('button').each(function(){
            var button = $(this)
            button.on('click', function(event){
                event.preventDefault();
                $.ajax({
                    'dataType': "json",
                    'url' : button.attr('data-listing-url'), 
                    'method' : 'POST',
                    'success' : function(data){
                                if (button.attr('data-target') === 'reject') {
                                    if (data.rejected) {
                                        button.html("<span style='color: red;'>✖︎</span>");
                                    } else {
                                        button.html("<span style='color: black;'>✖︎</span>");
                                    }
                                }
                                if (button.attr('data-target') === 'score') {
                                    button.siblings('span.score').text(data.score)
                                }
                                if (button.attr('data-target') === 'star') {
                                    if (data.starred) {
                                        button.html("<span style='color: gold;'>⭑</span>")
                                    } else {
                                        button.html("<span style='color: black;'>⭑</span>")
                                    }
                                }
                                if (button.attr('data-next-listing') !== '') {
                                    setTimeout(function(){
                                    $(location).attr('href', button.attr('data-next-listing'));
                                    }, 100);
                                }
                            }
                    });
                });
            })
    });
    
    
    });