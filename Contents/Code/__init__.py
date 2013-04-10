CBS_LIST = 'http://www.cbs.com/video/'
CAROUSEL_URL = 'http://www.cbs.com/carousels/videosBySection/%s/0/15/'
CLASSICS_URL = 'http://www.cbs.com/shows/%s/videos_more/season/0/videos/%s/%s'
CATEGORIES = [
	{"title": "Primetime",	"label": "primetime"},
	{"title": "Daytime",	"label": "daytime"},
	{"title": "Late Night",	"label": "latenight"},
	{"title": "Specials",	"label": "specials"},
    {"title": "Classics",   "label": "classics"}
]

RE_S_EP_DURATION = Regex('S(\d+)? Ep(\d+)? \((\d+:\d+)\)')
RE_SAFE_TITLE = Regex('/classics/(.+?)/video')
RE_SEASON = Regex('Season ([0-9]+),')

EXCLUDE_SHOWS = ('CBS Evening News')

####################################################################################################
def Start():

	ObjectContainer.title1 = 'CBS'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0'

####################################################################################################
@handler('/video/cbs', 'CBS')
def MainMenu():

	oc = ObjectContainer()

	for category in CATEGORIES:
        if category['title'] == 'Classics':
            classics = True
        else:
            classics = False    
		oc.add(DirectoryObject(
			key = Callback(Shows, title=category['title'], category=category['label'], classics=classics),
			title = category['title']
		))

	return oc

####################################################################################################
@route('/video/cbs/shows')
def Shows(title, category, classics=False):

	oc = ObjectContainer(title2=title)

	for item in HTML.ElementFromURL(CBS_LIST).xpath('//div[@id="%s"]//div[@id="show_block_interior"]' % category):
		title = item.xpath('./a/img/@alt')[0]

		if title in EXCLUDE_SHOWS:
			continue

		url = item.xpath('./a/@href')[0]
		if not url.startswith('http://'):
			url = 'http://www.cbs.com/%s' % url.lstrip('/')
		if not url.endswith('/video/'):
			url = '%s/video/' % url.rstrip('/')

		thumb = item.xpath('./a/img/@src')[0]
		if not thumb.startswith('http://'):
			thumb = 'http://www.cbs.com/%s' % thumb.lstrip('/')
        
        if classics:
            oc.add(DirectoryObject(
    		    key = Callback(ClassicCategories, title=title, url=url, thumb=thumb),
			    title = title,
			    thumb = Resource.ContentsOfURLWithFallback(thumb)
		        ))
        else:
		    oc.add(DirectoryObject(
			    key = Callback(Category, title=title, url=url, thumb=thumb),
			    title = title,
			    thumb = Resource.ContentsOfURLWithFallback(thumb)
		        ))

	return oc

####################################################################################################
@route('/video/cbs/category')
def Category(title, url, thumb):

	oc = ObjectContainer(title2=title)

	try:
		html = HTML.ElementFromURL(url)
	except:
		return ObjectContainer(header="Empty", message="Can't find video's for this show.")

	for carousel in html.xpath('//div[starts-with(@id, "id-carousel")]/@id'):
		json_url = CAROUSEL_URL % carousel.split('-')[-1]
		json_obj = JSON.ObjectFromURL(json_url)

		if json_obj['success']:
			title = json_obj['result']['title']

			oc.add(DirectoryObject(
				key = Callback(Video, title=title, json_url=json_url),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(thumb)
			))

	return oc

####################################################################################################
@route('/video/cbs/video')
def Video(title, json_url):

	oc = ObjectContainer(title2=title)

	if title.lower() == 'full episodes':
		type = 'episode'
	else:
		type = 'video'

	for video in JSON.ObjectFromURL(json_url)['result']['videos']:
		title = video['title'].split(' - ', 1)[-1]

		thumb = video['thumb']['large']
		if not thumb:
			thumb = video['thumb']['small']

		url = video['url']
		if not url.startswith('http://'):
			url = 'http://www.cbs.com/%s' % url.lstrip('/')

		if type == 'video':
			oc.add(VideoClipObject(
				url = url,
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(thumb)
			))
		elif type == 'episode':
			show = video['series_title']

			try:
				html = HTML.ElementFromURL(url)
			except:
				continue

			summary = html.xpath('//meta[@property="og:description"]/@content')[0]
			episode_info = html.xpath('//div[@class="title"]/span/text()')[0]

			(season, episode, duration) = RE_S_EP_DURATION.search(episode_info).groups()
			season = int(season) if season is not None else None
			index = int(episode) if episode is not None else None
			duration = Datetime.MillisecondsFromString(duration) if duration is not None else None

			oc.add(EpisodeObject(
				url = url,
				show = show,
				title = title,
				summary = summary,
				season = season,
				index = index,
				duration = duration,
				thumb = Resource.ContentsOfURLWithFallback(thumb)
			))

	return oc
####################################################################################################
@route('/video/cbs/category')
def ClassicCategories(title, url, thumb):

    oc = ObjectContainer(title2=title)
    
    video_types = [
        {'title': 'Full Episodes',  'label': 'episodes'},
        {'title': 'Clips',          'label':, 'clips'}
                ]
	for category in video_types:
        oc.add(DirectoryObject(
				key = Callback(Classics, title=title, url=url, thumb=thumb, label=category['label']),
				title = category['title'],
				thumb = Resource.ContentsOfURLWithFallback(thumb)
			))

	return oc
####################################################################################################
@route('/video/cbs/category')
def Classics(title, url, thumb, label, offset=0):

    oc = ObjectContainer(title2=title)
    
    safe_title = RE_SAFE_TITLE.search(url).group(1)
	json_url = CLASSICS_URL % (safe_title, label, offset)
    try:
		json_obj = JSON.ObjectFromURL(json_url)
        if json_obj['success']:
            html = HTML.ElementFromString(json_obj['html'])
        else:
            raise e
	except:
		return ObjectContainer(header="Empty", message="Can't find video's for this show.")
    
    for entry in html.xpath('//div[@class="video-content-item"]'):
        video_url = html.xpath('.//a')[0].get('href')
        if not video_url.startswith('http://'):
    		viddeo_url = 'http://www.cbs.com/%s' % video_url.lstrip('/')
		video_title = html.xpath('.//div[@class="video-content-title"]')[0].text
        video_thumb = html.xpath('.//div[@class="video-content-thumb-container"]//img')[0].get('src')
        summary = html.xpath('.//div[@class="video-content-description"]')[0].text
        duration = html.xpath('.//div[@class="video-content-duration"][0]//text()')[1].strip('()')
        durationMS = Datetime.MillisecondsFromString(duration)
        airdate = html.xpath('.//div[@class="video-content-air-date"][0]//text()')[1].strip(': ->')
        airdate = Datetime.ParseDate(airdate).date
        
        if label == 'episodes':
            season = RE_SEASON.search(html.xpath('div[@class="video-content-season-info"]')[0].text).group(1)
            oc.add(EpisodeObject(
                url = video_url,
                title = video_title,
                summary = summary,
                originally_available_at = airdate,
                duration = durationMS,
                thumb = Resource.ContentsOfURLWithFallback(video_thumb),
                season = int(season),
                show = title
                ))
        else:
            oc.add(VideoClipObject(
                url = video_url,
                title = video_title,
                summary = summary,
                originally_available_at = airdate,
                duration = durationMS,
                thumb = Resource.ContentsOfURLWithFallback(video_thumb)
                ))

	if json_obj['more']:
        offset = json_obj['next']
        oc.add(NextPageObject(
				key = Callback(Classics, title=title, url=url, thumb=thumb, label=label, offset=offset)
			))

	return oc

####################################################################################################
