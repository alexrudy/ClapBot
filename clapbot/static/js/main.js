$(document).ready(function(){
    $('.datatables').each(function(){$(this).dataTable({
    paging: false,
    autoWidth: false,
    ordering: false
    }
    )});
});
