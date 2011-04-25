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
    
        newIMG.draggable({stop: function (event, ui) {
            updateServer(event, ui)}
        });
        
        newIMG.width(function (i,width) {
           return width > 150 ? 150 : width;
        });
        window.console.log(newIMG);
    };

    function updateServer(event, ui) {
        window.console.log($('#topic-name').text());
        window.console.log(ui.position);
        window.console.log(event.target.src);
        $.post('/topic/update_topic/',
            {
                topic_name: $('#topic-name').text(),
                image_src: event.target.src,
                image_left: ui.position.left,
                image_top: ui.position.top 
            }
        );
    };


    // Listen for drag events
    $('.ui-draggable').bind("dragstop", function(event, ui) {
        alert('done drag');
    }); 
}
