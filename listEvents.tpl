<html>
	<head>
		<meta http-equiv="Content-type" content="text/html; charset=utf-8">
		
		<title>crowded</title>
		<link rel="stylesheet" href="/static/css/basic.css" type="text/css" />
		<link rel="stylesheet" href="/static/css/galleriffic-2.css" type="text/css" />

	</head>
	<body>
		<div id="page">
			<div id="container">
				<h1><a href="index.html">Current Events</a></h1>
				%if len(tagEvents) > 0:
					<h2>Tag Events</h1>
						</br>
						<table class="gridtable">
						<tr>
							<th>Event Id</th><th>Created</th><th>Splash Page</th>
						</tr>
						%for event in tagEvents:
							<tr>
								<td>{{event['objectId']}}</td><td>{{event['start']}}</td><td><a href="/events/{{event['objectId']}}">Media</a></td>
							</tr>
	  				    %end
						</table>
						</br>
				%end
				</br>
				</br>
				%if len(geoEvents) > 0:
					<h2>Geographic Events</h1>
					</br>
					<table class="gridtable">
					<tr>
						<th>Event Id</th><th>Created</th><th>Lat</th><th>Lon</th><th>Radius (m)</th><th>Splash Page</th>
					</tr>
					%for event in geoEvents:
						<tr>
							<td>{{event['objectId']}}</td><td>{{event['start']}}</td><td>{{event['loc'][1]}}</td><td>{{event['loc'][0]}}</td><td>{{event['radius_m']}}</td><td><a href="/events/{{event['objectId']}}">Media</a></td>
						</tr>
  				    %end
					</table>
				%end
				<div style="clear: both;"></div>
			</div>
		</div>
		
		<div id="footer"> Crowded | A crowd sourced view of events as they happen </div>

	</body>
</html>