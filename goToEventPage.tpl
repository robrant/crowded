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
				<h1><a href="index.html">Crowded Event Built</a></h1>
				</br>
				</br>
				<h3>Your event has been created. It's object ID is: {{objectId}} </h3>
				</br>
				<h4> Take a look at <a href="{{eventPage}}">media for your event</a> </h4>
				</br>
				<h4> Your event will last 24 hours in crowded before being purged.</h4>
				</br>				
				<h4>Take a look at <a href="{{helpPage}}">this help page</a> to see how you or your app can create events in crowded.</h4>
				</br>				

				<div style="clear: both;"></div>
			</div>
		</div>
		
		<div id="footer"> Crowded | A crowd sourced view of events as they happen </div>

	</body>
</html>