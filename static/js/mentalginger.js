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
    
    //Hit enter to search.
    $('.searchBox').live('keydown',function(ev) {
        if (ev.keyCode == 13)
            $(this).parent().find('input[type=submit]').click();
    });
}


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
    return newIMG;
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


function createImageFromModel(image_src, image_left, image_top) {
    var img = new Image();
    img.src = image_src;
    img.width = 150;
    var attachedImage = addImageToCollage(img);
    window.console.log(image_left);
    attachedImage.css('left', image_left + 'px');
    attachedImage.css('top', image_top + 'px');
};
