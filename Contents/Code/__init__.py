####################################################################################################

NAME = 'CBS'
ART  = 'art-default.jpg'
ICON = 'icon-default.png'

CBS_LIST = 'http://www.cbs.com/video/'

API_URL = "http://api.cnet.com/restApi/v1.0/videoSearch?categoryIds=%s&orderBy=productionDate~desc,createDate~desc&limit=20&iod=images,videoMedia,relatedLink,breadcrumb,relatedAssets,broadcast,lowcache&partTag=cntv&showBroadcast=true"
API_NAMESPACE  = {'l':'http://api.cnet.com/rest/v1.0/ns'}

SHOWNAME_LIST = 'http://cbs.feeds.theplatform.com/ps/JSON/PortalService/1.6/getReleaseList?PID=GIIJWbEj_zj6weINzALPyoHte4KLYNmp&startIndex=1&endIndex=500&query=contentCustomBoolean|EpisodeFlag|%s&query=CustomBoolean|IsLowFLVRelease|false&query=contentCustomText|SeriesTitle|%s&query=servers|%s&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&field=encodingProfile&contentCustomField=label'
CBS_SMIL = 'http://release.theplatform.com/content.select?format=SMIL&Tracking=true&balance=true&pid=%s'
SERVERS = ['CBS%20Production%20Delivery%20h264%20Akamai',
           'CBS%20Production%20News%20Delivery%20Akamai%20Flash',
           'CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash',
           'CBS%20Production%20Entertainment%20Delivery%20Akamai%20Flash%20Progressive',
           'CBS%20Delivery%20Akamai%20Flash']
CATEGORIES = [{"title":"Primetime","label":"primetime"},{"title":"Daytime","label":"daytime"},
                {"title":"Late Night","label":"latenight"},{"title":"Classics","label":"classics"},
                {"title":"Specials","label":"specials"},{"title":"Web Originals","label":"originals"}]

CAROUSEL_URL = 'http://www.cbs.com/carousels/%s/video/%s/%s/0/100/'

API_TITLES = ["48 Hours Mystery"]
API_IDS = {"48 Hours Mystery":{"episodes":"503443", "clips":"18559"}}

RE_FULL_EPS = Regex("\.loadUpCarousel\('Full Episodes','(0_video_.+?)', '(.+?)', ([0-9]+), .+?\);", Regex.DOTALL|Regex.IGNORECASE)
RE_CLIPS = Regex("loadUpCarousel\('Newest Clips','(0_video_.+?)', '(.+?)', ([0-9]+), .+?\);", Regex.DOTALL)

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
		if 'http://www.cbs.com/' not in url:
			url = 'http://www.cbs.com' + url

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
	Log(display_title)
	if display_title not in API_TITLES:
		oc.add(DirectoryObject(key=Callback(Videos, full_episodes='true', title=title, display_title=display_title, url=url), title='Full Episodes'))
		oc.add(DirectoryObject(key=Callback(Videos, full_episodes='false', title=title, display_title=display_title, url=url), title='Clips'))
	else:
		oc.add(DirectoryObject(key=Callback(APIVideos, full_episodes='true', title=title, display_title=display_title, url=url), title='Full Episodes'))
		oc.add(DirectoryObject(key=Callback(APIVideos, full_episodes='false', title=title, display_title=display_title, url=url), title='Clips'))
	return oc

####################################################################################################
def Videos(full_episodes, title, display_title, url):
	oc = ObjectContainer(title2=display_title)
	page = HTTP.Request(url).content
	if full_episodes == 'true':
		episodes = []
		request_params = RE_FULL_EPS.findall(page)
		if request_params != None:
			for i in range(len(request_params)):
				show_id = request_params[i][2]
				server = request_params[i][0]
				hash = request_params[i][1]
				episode_list = JSON.ObjectFromURL(CAROUSEL_URL % (show_id, server, hash))
				for episode in episode_list['itemList']:
					video_title = episode['title']
					date = Datetime.FromTimestamp(int(episode['airDate'])/1000).date()
					summary = episode['description']
					video_url = episode['url']
					index = int(episode['episodeNum'])
					season = int(episode['seasonNum'])
					show = episode['seriesTitle']
					duration = int(episode['duration'])*1000
					content_rating = episode['rating']
					thumbs = SortImages(episode['thumbnailSet'])
					episode_string = "S%sE%s - %s" % (season, index, video_title)
					if episode_string not in episodes:
						oc.add(EpisodeObject(url=video_url, title=video_title, show=show, index=index, season=season, summary=summary,
							duration=duration, originally_available_at=date, content_rating=content_rating,
							thumb=Resource.ContentsOfURLWithFallback(url=thumbs, fallback=ICON)))
						episodes.append(episode_string)
					else:
						pass
                else:
			pass
		if len(oc) == 0:
			return OlderVideos(full_episodes=full_episodes, title=title, display_title=display_title, url=url)
		else:
			oc.add(DirectoryObject(key=Callback(OlderVideos, full_episodes=full_episodes, title=title, display_title=display_title, url=url), title="Older Episodes"))
	else:
		request_params = RE_CLIPS.findall(page)
		if request_params != None:
			for i in range(len(request_params)):
				show_id = request_params[i][2]
				server = request_params[i][0]
				hash = request_params[i][1]
				clip_list = JSON.ObjectFromURL(CAROUSEL_URL % (show_id, server, hash))
				for clip in clip_list['itemList']:
					video_title = clip['title']
					date = Datetime.FromTimestamp(int(clip['pubDate'])/1000).date()
					summary = clip['description']
					video_url = clip['url']
					duration = int(clip['duration'])*1000
					thumbs = SortImages(clip['thumbnailSet'])
					oc.add(VideoClipObject(url=video_url, title=video_title, summary=summary, duration=duration, originally_available_at=date,
						thumb=Resource.ContentsOfURLWithFallback(url=thumbs, fallback=ICON)))
		else:
			pass
		if len(oc) == 0:
			return OlderVideos(full_episodes=full_episodes, title=title, display_title=display_title, url=url)
		else:
			oc.add(DirectoryObject(key=Callback(OlderVideos, full_episodes=full_episodes, title=title, display_title=display_title, url=url), title="Older clips"))
        
	return oc
####################################################################################################
def OlderVideos(full_episodes, title, display_title, url):
	oc = ObjectContainer(title2=display_title)
	show_title = title
	processed_titles = []
	
	for server in SERVERS:
		feed_url = SHOWNAME_LIST % (full_episodes, show_title, server)
		Log(' --> Checking server: ' + server)
		Log(' --> URL: ' + url)

		try:
			feeds = JSON.ObjectFromURL(feed_url)
			encoding = ''

			for item in feeds['items']:
				title = item['contentCustomData'][0]['value']

				if title not in processed_titles:
					if "HD" in item['encodingProfile']:
						encoding = " - HD " + item['encodingProfile'][3:8].replace(' ', '')
					else:
						encoding = ''
					video_title = title + str(encoding)
					pid = item['PID']
					video_url = url + '?play=true&pid=' + pid
					summary = item['description'].replace('In Full:', '')
					duration = item['length']
					thumb = item['thumbnailURL']
					airdate = int(item['airdate'])/1000
					originally_available_at = Datetime.FromTimestamp(airdate).date()
                    
					if full_episodes == "true":
						oc.add(EpisodeObject(url=video_url, show=display_title, title=video_title, summary=summary, duration=duration,
							originally_available_at=originally_available_at, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
					else:
						oc.add(VideoClipObject(url=video_url, title=video_title, summary=summary, duration=duration,
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
def APIVideos(full_episodes, title, display_title, url):
	oc = ObjectContainer(title2=display_title)

	if full_episodes == 'true':
		data = XML.ElementFromURL(API_URL % API_IDS[display_title]['episodes'])
		for episode in data.xpath('//l:Video', namespaces=API_NAMESPACE):
			video_url = episode.xpath('.//l:CBSURL', namespaces=API_NAMESPACE)[0].text
			title = episode.xpath('.//l:Title', namespaces=API_NAMESPACE)[0].text
			date = Datetime.ParseDate(episode.xpath('.//l:ProductionDate', namespaces=API_NAMESPACE)[0].text).date()
			summary = episode.xpath('.//l:Description', namespaces=API_NAMESPACE)[0].text
			duration = int(episode.xpath('.//l:LengthSecs', namespaces=API_NAMESPACE)[0].text)*1000
			images = episode.xpath('.//l:Images/l:Image', namespaces=API_NAMESPACE)
			thumbs = SortImagesFromAPI(images)
			show = display_title
			rating = episode.xpath('.//l:ContentRatingOverall', namespaces=API_NAMESPACE)[0].text
			season = int(episode.xpath('.//l:SeasonNumber', namespaces=API_NAMESPACE)[0].text)
			index = int(episode.xpath('.//l:EpisodeNumber', namespaces=API_NAMESPACE)[0].text)
			
			oc.add(EpisodeObject(url=video_url, title=title, show=show, summary=summary, originally_available_at=date, duration=duration,
				content_rating=rating, season=season, index=index, thumb=Resource.ContentsOfURLWithFallback(url=thumbs, fallback='icon-default.png')))
	else:
		data = XML.ElementFromURL(API_URL % API_IDS[display_title]['clips'])
		for clip in data.xpath('//l:Video', namespaces=API_NAMESPACE):
			video_url = clip.xpath('.//l:CBSURL', namespaces=API_NAMESPACE)[0].text
			title = clip.xpath('.//l:Title', namespaces=API_NAMESPACE)[0].text
			date = Datetime.ParseDate(clip.xpath('.//l:ProductionDate', namespaces=API_NAMESPACE)[0].text).date()
			summary = clip.xpath('.//l:Description', namespaces=API_NAMESPACE)[0].text
			duration = int(clip.xpath('.//l:LengthSecs', namespaces=API_NAMESPACE)[0].text)*1000
			images = clip.xpath('.//l:Images/l:Image', namespaces=API_NAMESPACE)
			thumbs = SortImagesFromAPI(images)
    
			oc.add(VideoClipObject(url=video_url, title=title, originally_available_at=date, duration=duration,summary = summary,
				thumb = Resource.ContentsOfURLWithFallback(url=thumbs, fallback='icon-default.png')))
			
	return oc
####################################################################################################
def SortImages(images=[]):

  sorted_thumbs = sorted(images, key=lambda thumb : int(thumb['height']), reverse=True)
  thumb_list = []
  for thumb in sorted_thumbs:
      thumb_list.append(thumb['url'])

  return thumb_list

####################################################################################################
def SortImagesFromAPI(images=[]):
  
  thumbs = []
  for image in images:
      height = image.get('height')
      url = image.xpath('./l:ImageURL', namespaces=API_NAMESPACE)[0].text
      thumbs.append({'height':height, 'url':url})

  sorted_thumbs = sorted(thumbs, key=lambda thumb : int(thumb['height']), reverse=True)
  thumb_list = []
  for thumb in sorted_thumbs:
      thumb_list.append(thumb['url'])

  return thumb_list