$(function() {
   $(".photo-card a").fancybox({
		helpers: {
			title : {
				type : 'float'
			}
		},
		afterShow: function() {
			var downloadUrl = $(this.element).attr('data-download');
			if(downloadUrl != undefined) {
				$('<a class="fancybox-download" href="' + downloadUrl + '"></a>').appendTo(this.outer);
			}
		},
		padding: 0
	});
});
