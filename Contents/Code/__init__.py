CBS_LIST = 'http://www.cbs.com/video/'
CAROUSEL_URL = 'http://www.cbs.com/carousels/videosBySection/%s/0/40/'
CATEGORIES = [
	{"title": "Primetime",	"label": "primetime"},
	{"title": "Daytime",	"label": "daytime"},
	{"title": "Late Night",	"label": "latenight"},
	{"title": "Specials",	"label": "specials"}
]

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
		oc.add(DirectoryObject(
			key = Callback(Shows, title=category['title'], category=category['label']),
			title = category['title']
		))

	return oc

####################################################################################################
@route('/video/cbs/shows')
def Shows(title, category):

	oc = ObjectContainer(title2=title)

	for item in HTML.ElementFromURL(CBS_LIST).xpath('//div[@id="%s"]//div[@id="show_block_interior"]' % category):
		title = item.xpath('./a/img/@alt')[0]

		url = item.xpath('./a/@href')[0]
		if not url.startswith('http://'):
			url = 'http://www.cbs.com/%s' % url.lstrip('/')
		if not url.endswith('/video/'):
			url = '%s/video/' % url.rstrip('/')

		thumb = item.xpath('./a/img/@src')[0]
		if not thumb.startswith('http://'):
			thumb = 'http://www.cbs.com/%s' % thumb.lstrip('/')

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

	for carousel in HTML.ElementFromURL(url).xpath('//div[starts-with(@id, "id-carousel")]/@id'):
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

	for video in JSON.ObjectFromURL(json_url)['result']['videos']:
		show = video['series_title']
		title = video['episode_title']

		thumb = video['thumb']['large']
		if not thumb:
			thumb = video['thumb']['small']

		url = video['url']
		if not url.startswith('http://'):
			url = 'http://www.cbs.com/%s' % url.lstrip('/')

		oc.add(EpisodeObject(
			url = url,
			show = show,
			title = title,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	return oc
