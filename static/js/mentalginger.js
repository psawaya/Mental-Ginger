function mentalGinger() {
    //Init!
    
    $('#flickrSearchButton').click(function() {
        $.ajax({
            url : '/search',
            'data' : {
                'tags' : $('#flickrSearch').val()
            },
            success: function(returnedHTML) {
                $('#searchResults').html(returnedHTML);
            }
        });
    });
    
    $('#searchResults').click(function(e) {
        if ($(e.target).hasClass('previewImage')) {
            addImageToCollage(e.target);
        }
    });
    
    function addImageToCollage(image) {
        var newIMG = $(image).clone();
        newIMG.removeClass('previewImage');
        
        $('#image-board').append(newIMG);
    
        newIMG.draggable();
        
        newIMG.width(function (i,width) {
           return width > 150 ? 150 : width;
        });
        window.console.log(newIMG);
    }
}
