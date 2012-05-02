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
CATEGORIES = [{"title":"Primetime","label":"primetime"},{"title":"Daytime","label":"daytime"},
                {"title":"Late Night","label":"latenight"},{"title":"Classics","label":"classics"},
                {"title":"Specials","label":"specials"},{"title":"Web Originals","label":"originals"}]
                
####################################################################################################
def Start():
	Plugin.AddPrefixHandler('/video/cbs', MainMenu, NAME, ICON, ART)

    ObjectContainer.art = R(ART)
	ObjectContainer.title1 = NAME
	DirectoryObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16'

####################################################################################################
def MainMenu():
	oc = ObjectContainer()
    for category in CATEGORIES:
        oc.add(DirectoryObject(key=Callback(Shows, title=category['title'], category=category['label']), title=category['title']))
	return oc

####################################################################################################
def Shows(title, category):
	oc = ObjectContainer(title2=title)

	for item in HTML.ElementFromURL(CBS_LIST).xpath('//div[@id="' + category + '"]//div[@id="show_block_interior"]'):
		title = item.xpath('.//img')[0].get('alt')
		display_title = title
        url = item.xpath('.//a')[0].get('href')

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

		oc.add(DirectoryObject(key=Callback(EpisodesAndClips, title=title, display_title=display_title, url=url), title=display_title))

	return oc

####################################################################################################
def EpisodesAndClips(title, display_title, url):
	oc = ObjectContainer(title2=display_title)
    oc.add(DirectoryObject(key=Callback(Videos, full_episodes='true', title=title, display_title=display_title, url=url), title='Full Episodes'))
    oc.add(DirectoryObject(key=Callback(Videos, full_episodes='false', title=title, display_title=display_title, url=url), title='Clips'))
	return oc

####################################################################################################
def OlderVideos(full_episodes, title, display_title, url):
	oc = ObjectContainer(title2=display_title)
	processed_titles = []

	for server in SERVERS:
		url = SHOWNAME_LIST % (hd, full_episodes, title, server)
		Log(' --> Checking server: ' + server)
		Log(' --> URL: ' + url)

		try:
			feeds = JSON.ObjectFromURL(url)
			encoding = ''

			for item in feeds['items']:
				title = item['contentCustomData'][0]['value']

				if title not in processed_titles:
					if hd == '':
						if "HD" in item['encodingProfile']:
							encoding = " - HD " + item['encodingProfile'][3:8].replace(' ', '')
						else:
							encoding = ''

					video_title = title + str(encoding)
					pid = item['PID']
					summary = item['description'].replace('In Full:', '')
					duration = item['length']
					thumb = item['thumbnailURL']
					airdate = int(item['airdate'])/1000
                    originally_available_at = Datetime.FromTimestamp(airdate).date()
                    
                    if full_episodes == "true":
                        oc.add(EpisodeObject(url=smil, show=display_title, title=video_title, summary=summary, duration=duration,
                            originally_available_at=originally_available_at, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
                    else:
                        oc.add(VideoClipObject(url=smil, title=video_title, summary=summary, duration=duration,
                            originally_available_at=originally_available_at, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))

					processed_titles.append(title)

			Log(' --> Success! Found ' + str(len(feeds['items'])) + ' items')
		except:
			Log(' --> Failed!')
			pass

	if len(oc) == 0:
		return ObjectContainer(header='Empty', message="There aren't any items")
	else:
		return oc

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

