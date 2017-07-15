$(document).ready(function(){
    $('.datatables').each(function(){
        var table = $(this).dataTable({
            paging: false,
            autoWidth: false,
            ordering: false,
            'autoWidth': false
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
                                        $('tr#listing-' + id).first().fadeOut(300, function(){table.row($(this)).remove();});
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
                                }
                        });
                    });
                });
            })
    });
    
    
    });