<html>
	<head>
		<meta http-equiv="Content-type" content="text/html; charset=utf-8">
		
		<title>crowded</title>
		<link rel="stylesheet" href="/static/css/basic.css" type="text/css" />
		<link rel="stylesheet" href="/static/css/galleriffic-2.css" type="text/css" />
		
		<script type="text/javascript" src="/static/js/jquery-1.3.2.js"></script>
		<script type="text/javascript" src="/static/js/jquery.galleriffic.js"></script>
		<script type="text/javascript" src="/static/js/jquery.opacityrollover.js"></script>
		
		<!-- We only want the thunbnails to display when javascript is disabled -->
		<script type="text/javascript">
			document.write('<style>.noscript { display: none; }</style>');
		</script>
	</head>
	<body>
		<div id="page">
			<div id="container">
				<h1><a href="index.html">{{header}}</a></h1>
				<h3>{{subHeader}}</h3>
				<h3>{{initiated}}</h3>
				<h4>{{associatedTags}}</h4>
				
				<!-- Start Advanced Gallery Html Containers -->
				<div id="gallery" class="content">
					<div id="controls" class="controls"></div>
					<div class="slideshow-container">
						<div id="loading" class="loader"></div>
						<div id="slideshow" class="slideshow"></div>
					</div>
					<div id="caption" class="caption-container"></div>
				</div>
				<div id="thumbs" class="navigation">
					<ul class="thumbs noscript">
						%for photo in photos:
							<li>
							<a class="thumb" name="leaf" href="{{photo['low_resolution']}}" title="{{photo['caption']}}">
								<img src="{{photo['thumbnail']}}" alt="{{photo['caption']}}" width="100" height="100" />
							</a>
							<div class="caption">
								<div class="download">
									<a href="{{photo['standard_resolution']}}">Original</a>
								</div>
								<div class="image-title">{{photo['dt']}}</div>
								<div class="image-desc">
								{{photo['caption']}}
									<p>
									{{photo['source']}}
									</p>
								</div>

							</div>
						</li>
					   %end
					</ul>
				</div>
				<div style="clear: both;"></div>
			</div>
		</div>
		
		<div id="footer"> Crowded | A crowd sourced view of events as they happen </div>
		<script type="text/javascript">
			jQuery(document).ready(function($) {
				// We only want these styles applied when javascript is enabled
				$('div.navigation').css({'width' : '300px', 'float' : 'left'});
				$('div.content').css('display', 'block');

				// Initially set opacity on thumbs and add
				// additional styling for hover effect on thumbs
				var onMouseOutOpacity = 0.67;
				$('#thumbs ul.thumbs li').opacityrollover({
					mouseOutOpacity:   onMouseOutOpacity,
					mouseOverOpacity:  1.0,
					fadeSpeed:         'fast',
					exemptionSelector: '.selected'
				});
				
				// Initialize Advanced Galleriffic Gallery
				var gallery = $('#thumbs').galleriffic({
					delay:                     2500,
					numThumbs:                 10,
					preloadAhead:              10,
					enableTopPager:            true,
					enableBottomPager:         true,
					maxPagesToShow:            7,
					imageContainerSel:         '#slideshow',
					controlsContainerSel:      '#controls',
					captionContainerSel:       '#caption',
					loadingContainerSel:       '#loading',
					renderSSControls:          true,
					renderNavControls:         true,
					playLinkText:              'Play Slideshow',
					pauseLinkText:             'Pause Slideshow',
					prevLinkText:              '&lsaquo; Previous Image',
					nextLinkText:              'Next Image &rsaquo;',
					nextPageLinkText:          'Next &rsaquo;',
					prevPageLinkText:          '&lsaquo; Prev',
					enableHistory:             false,
					autoStart:                 false,
					syncTransitions:           true,
					defaultTransitionDuration: 900,
					onSlideChange:             function(prevIndex, nextIndex) {
						// 'this' refers to the gallery, which is an extension of $('#thumbs')
						this.find('ul.thumbs').children()
							.eq(prevIndex).fadeTo('fast', onMouseOutOpacity).end()
							.eq(nextIndex).fadeTo('fast', 1.0);
					},
					onPageTransitionOut:       function(callback) {
						this.fadeTo('fast', 0.0, callback);
					},
					onPageTransitionIn:        function() {
						this.fadeTo('fast', 1.0);
					}
				});
			});
		</script>
	</body>
</html>