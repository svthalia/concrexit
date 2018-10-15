$(function() {
   $(".photo-card a").fancybox({
		helpers: {
			title : {
				type : 'float'
			}
		},
		afterShow: function() {
			var downloadUrl = $(this.element).attr('data-download');
			if(downloadUrl !== undefined) {
				$('<a class="btn btn-primary fancybox-download" href="' + downloadUrl + '"><i class="fas fa-download"></i></a>').appendTo(this.outer);
			}
		},
		padding: 0,
        tpl: {
		    closeBtn: '<a title="Close" class="btn btn-primary fancybox-close" href="javascript:;"><i class="fas fa-times"></i></a>',
            next: '<a title="Next" class="fancybox-nav fancybox-next" href="javascript:;"><span class="btn btn-primary"><i class="fas fa-arrow-right"></i></span></a>',
            prev: '<a title="Previous" class="fancybox-nav fancybox-prev" href="javascript:;"><span class="btn btn-primary"><i class="fas fa-arrow-left"></i></span></a>'
        }
	});
});
