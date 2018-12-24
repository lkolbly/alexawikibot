from bs4 import BeautifulSoup
import requests
import difflib
import datetime
import xmltodict
import myawis
import pywikibot
import pywikibot.xmlreader
from pywikibot.pagegenerators import XMLDumpPageGenerator

secrets = open("secrets").read().split("\n")[0].split(",")
ACCESS_KEY = secrets[0]
SECRET_KEY = secrets[1]

site = pywikibot.Site()
awis = myawis.CallAwis(ACCESS_KEY, SECRET_KEY)

def get_alexa_pubapi(url):
	import pprint
	r = requests.get("http://data.alexa.com/data?cli=10&dat=snbamz&url={}".format(url))
	xml = xmltodict.parse(r.text)

	r = requests.get("http://www.alexa.com/siteinfo/{}".format(url))
	soup = BeautifulSoup(r.text, 'html.parser')

	return xml["ALEXA"]["SD"][1]["REACH"]["@RANK"], xml["ALEXA"]["SD"][1]["RANK"]["@DELTA"], soup.title.string

def get_alexa(url):
	import pprint
	o = awis.urlinfo(url)
	#pprint.pprint(myawis.flatten_urlinfo(o))
	#print(url, o)
	xml = xmltodict.parse(str(o))
	xml = xml["aws:UrlInfoResponse"]["aws:Response"]["aws:UrlInfoResult"]["aws:Alexa"]

	r = requests.get("http://www.alexa.com/siteinfo/{}".format(url))
	soup = BeautifulSoup(r.text, 'html.parser')

	#pprint.pprint(xml)
	#rank = int(xml["aws:TrafficData"]["aws:Rank"])
	#print(url, rank)
	# This *should* be a 3-month lookback (the first element of the UsageStatistic array)
	try:
		rank = xml["aws:TrafficData"]["aws:UsageStatistics"]["aws:UsageStatistic"][0]["aws:Rank"]
		return rank["aws:Value"], rank["aws:Delta"], soup.title.string
	except:
		print("Failed to get data for {}".format(url))
		pprint.pprint(xml)

def get_field(infobox, fieldname):
	for field in infobox[1]:
		if field.startswith(fieldname+"="):
			return field

def parse_url(url):
	'''
	Possibilities:
	{{url|http://<domain>}} (w/ optional further vertical bars)
	{{url|<domain>}}
	[http://<domain>/ <domain>]
	'''
	url = url.lower()
	if url.startswith("{{url"):
		url = url.split("|")[1].strip("{}")
		if url.startswith("http://") or url.startswith("https://"):
			url = url.split("//")[1]
			url = url.split("/")[0]
		return url
	if url.startswith("[http"):
		url = url.split("//")[1]
		url = url.split("/")[0]
		return url
	pass

def update_page(page):
	templates = page.templatesWithParams()
	for template in templates:
		if template[0].title() == "Template:Infobox website":
			url = get_field(template, "url")
			alexa = get_field(template, "alexa")
			if url == None or alexa == None:
				print("{} has url={} alexa={}".format(page.title(), url, alexa))
				continue
			url = "=".join(url.split("=")[1:])

			# Parse a usable URL
			domain = parse_url(url)
			if domain == None:
				print("Couldn't parse domain for {}".format(url))
				continue

			# Strip off the www
			if domain.split(".")[0] == "www":
				domain = ".".join(domain.split(".")[1:])

			# @TODO: Subdomains aren't handled by alexa properly (the sub domain is stripped off?)
			if domain.count(".") > 1:
				continue
			ranking = get_alexa(domain)
			if ranking == None:
				print("Failed on url {}".format(url))
				continue
			rank, delta, sitetitle = ranking

			# Format the new alexa tag
			# @TODO: What does "IncreaseNegative" etc. mean?
			if delta[0] == '+':
				signal = "Decrease"
			elif delta[0] == '-':
				signal = "Increase"
			else:
				signal = "steady"
			now = datetime.datetime.now()
			y = now.year
			m = now.month
			d = now.day
			new_alexa = """{{{{{}}}}} {:,} ({{{{as of|{}|{}|{}}}}})<ref name="alexa">{{{{cite web|url= http://www.alexa.com/siteinfo/{} | publisher= [[Alexa Internet]] |title={} |accessdate= {}-{}-{} }}}}</ref> <!-- Updated monthly by LkolblyBot --> """.format(signal, int(rank), y, m, d, domain, sitetitle, y, m, d)

			print(domain)
			current_alexa = "=".join(alexa.split("=")[1:])
			print("Current alexa: {}".format(current_alexa))
			print("New alexa:     {}".format(new_alexa))
			newtext = page.text.replace(current_alexa, new_alexa)
			import sys
			sys.stdout.writelines(difflib.context_diff(list(map(lambda s: s+"\n", page.text.split("\n"))), list(map(lambda s: s+"\n", newtext.split("\n")))))
			print()
			print()

			#page.text = newtext
			#page.save("Update Alexa ranking")

if __name__ == "__main__":
	for pagetitle in open("../potential_alexas").readlines():
		update_page(pywikibot.Page(site, pagetitle))
	#print(get_alexa("darwinawards.com"))

	#for url in [
	#	"{{url|http://www.darwinawards.com/}}",
	#	"{{URL|ethnologue.com}}",
	#	"{{URL|www.google.com|Google.com}}",
	#	"[http://foldoc.org/ foldoc.org]"
	#]:
	#	print(parse_url(url))
