import datetime

####################################################################################################

NAME = 'CBS'
ART  = 'art-default.jpg'
ICON = 'icon-default.png'

CBS_LIST = 'http://www.cbs.com/video/'
SHOWNAME_LIST = 'http://cbs.feeds.theplatform.com/ps/JSON/PortalService/1.6/getReleaseList?PID=GIIJWbEj_zj6weINzALPyoHte4KLYNmp&startIndex=1&endIndex=500%s&query=contentCustomBoolean|EpisodeFlag|%s&query=CustomBoolean|IsLowFLVRelease|false&query=contentCustomText|SeriesTitle|%s&query=servers|%s&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&field=encodingProfile&contentCustomField=label'
CBS_SMIL = 'http://release.theplatform.com/content.select?format=SMIL&Tracking=true&balance=true&pid=%s'
SERVERS = ['CBS%20Production%20Delivery%20h264%20Akamai',
           'CBS%20Production%20News%20Delivery%20Akamai%20Flash',
           'CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash',
           'CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash%20Progressive',
           'CBS%20Delivery%20Akamai%20Flash']

####################################################################################################
def Start():
	Plugin.AddPrefixHandler('/video/cbs', MainMenu, NAME, ICON, ART)

	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')

	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	MediaContainer.viewGroup = 'InfoList'
	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16'

####################################################################################################
def MainMenu():
	dir = MediaContainer(viewGroup='List')
	dir.Append(Function(DirectoryItem(Shows, title='Primetime'), category='primetime'))
	dir.Append(Function(DirectoryItem(Shows, title='Daytime'), category='daytime'))
	dir.Append(Function(DirectoryItem(Shows, title='Late Night'), category='latenight'))
	dir.Append(Function(DirectoryItem(Shows, title='Classics'), category='classics'))
	dir.Append(Function(DirectoryItem(Shows, title='Specials'), category='specials'))
	dir.Append(PrefsItem(title='Preferences...', thumb=R('icon-prefs.png')))
	return dir

####################################################################################################
def Shows(sender, category):
	dir = MediaContainer(viewGroup='List', title2=sender.itemTitle)

	for item in HTML.ElementFromURL(CBS_LIST).xpath('//div[@id="' + category + '"]//span'):
		title = item.xpath('./..//img')[0].get('alt')
		display_title = title

		### Naming differences
		if title == 'Late Show With David Letterman':
			title = 'Late Show'

		if title == 'The Late Late Show with Craig Ferguson':
			title = 'The Late Late Show'

		if title == 'Star Trek: The Original Series':
			title = 'Star Trek Remastered'
			display_title += ' (HD only)' ### THESE ARE HD FEEDS - NEED TO FIND LOWER QUALITY

		if title == '48 Hours Mystery':
			title = '48 Hours'

		if title == 'CSI: Crime Scene Investigation':
			title = 'CSI:'

		if 'SURVIVOR' in title:
			title = 'Survivor'

		if title == 'The Bold And The Beautiful':
			title = 'Bold and the Beautiful'

		if title == 'The Young And The Restless':
			title = 'Young and the Restless'

		if title in ['Live on Letterman']:
			continue ### THESE ARE NOT ACTUAL SHOWS AND ARE EXCLUDED

		if 'GRAMMY' in title:
			title = 'Grammys'

		title = title.replace(' ', '%20').replace('&', '%26').replace("'", '')

		dir.Append(Function(DirectoryItem(EpisodesAndClips, title=display_title), title=title, display_title=display_title))

	if category == 'classics': ### THESE ARE HIDDEN FEEDS (MIGHT NEED TO CREATE A SEPARATE CATEGORY SOON)
		dir.Append(Function(DirectoryItem(EpisodesAndClips, title='*The Three Stooges'), title='The%20Three%20Stooges%20Show', display_title='The Three Stooges'))
		dir.Append(Function(DirectoryItem(EpisodesAndClips, title='*Robotech'), title='Robotech', display_title='Robotech'))

	return dir

####################################################################################################
def EpisodesAndClips(sender, title, display_title):
	dir = MediaContainer(viewGroup='List', title2=sender.itemTitle)
	dir.Append(Function(DirectoryItem(Videos, title='Full Episodes'), full_episodes='true', title=title, display_title=display_title))
	dir.Append(Function(DirectoryItem(Videos, title='Clips'), full_episodes='false', title=title, display_title=display_title))
	return dir

####################################################################################################
def Videos(sender, full_episodes, title, display_title):
	dir = MediaContainer(title2=display_title)

	if Prefs['hd']:
		hd = ''
	else:
		hd = '&query=CustomBoolean|IsHDRelease|false'

	for server in SERVERS:
		url = SHOWNAME_LIST % (hd, full_episodes, title, server)
		Log(' --> Checking server: ' + server)
		Log(' --> URL: ' + url)

		try:
			feeds = JSON.ObjectFromURL(url)
			encoding = ''

			for item in feeds['items']:
				if hd == '':
					if "HD" in item['encodingProfile']:
						encoding = " - HD " + item['encodingProfile'][3:8].replace(' ', '')
					else:
						encoding = ''

				video_title = item['contentCustomData'][0]['value'] + str(encoding)
				pid = item['PID']
				summary = item['description'].replace('In Full:', '')
				duration = item['length']
				thumb = item['thumbnailURL']
				airdate = int(item['airdate'])/1000
				subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
				dir.Append(Function(VideoItem(PlayVideo, title=video_title, subtitle=subtitle, summary=summary, thumb=Function(GetThumb, url=thumb), duration=duration), pid=pid))

			Log(' --> Success! Found ' + str(len(feeds['items'])) + ' items')
		except:
			Log(' --> Failed!')
			pass

	if len(dir) == 0:
		return MessageContainer('Empty', "There aren't any items")
	else:
		return dir

####################################################################################################
def PlayVideo(sender, pid):
	smil = HTTP.Request(CBS_SMIL % pid).content
	player = smil.split('ref src')
	player = player[2].split('"')
	if '.mp4' in player[1]:
		player = player[1].replace('.mp4', '')
		clip = player.split(';')
		clip = 'mp4:' + clip[4]
	else:
		player = player[1].replace('.flv', '')
		clip = player.split(';')
		clip = clip[4]
	return Redirect(RTMPVideoItem(player, clip))

####################################################################################################
def GetThumb(url):
	try:
		data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))
