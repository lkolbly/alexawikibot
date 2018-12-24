import xml.etree.ElementTree as ET
import sys
import re

currentPage = None

NS = "{http://www.mediawiki.org/xml/export-0.10/}"

def handle_start_page(elem):
	pass

def handle_title(elem):
	global currentPage
	currentPage = elem.text
	#print(currentPage)
	pass

def parse_text(text, offset=0):
	''' Parse the text into the (potentially recursive) {{...}} segments '''
	res = [""]
	#for i in range(offset, len(text)-1):
	i = offset
	while i < len(text) - 1:
		if text[i:i+2] == "{{" or text[i:i+2] == "[[":
			brace = text[i]
			sub_res, i = parse_text(text, i+2)
			sub_res = [brace] + sub_res
			res.append(sub_res)
			res.append("")
		elif text[i:i+2] == "}}" or text[i:i+2] == "]]":
			return list(filter(lambda s: len(s) > 0, res)), i+1
			pass
		else:
			res[-1] += text[i]
		i += 1
	return list(filter(lambda s: len(s) > 0, res)), len(text)

def print_ast(ast, indent=0):
	for elem in ast:
		if isinstance(elem, list):
			print_ast(elem, indent+2)
		else:
			print("-"*indent, elem.split("\n")[0][:80].strip("\r\n"))

def recombine_ast(ast):
	close_braces = {
		"{": "}",
		"[": "]",
	}
	res = ast[0] + ast[0]
	for part in ast[1:]:
		if isinstance(part, list):
			res += recombine_ast(part)
		else:
			res += part
	return res + close_braces[ast[0]]*2

def process_infobox(box):
	import json
	print(json.dumps(box, indent=2))

	# Divide it into the sections
	res = [""]
	for part in box[1:]:
		if isinstance(part, list):
			res[-1] += recombine_ast(part)
		else:
			sections = part.split("|")
			res[-1] += sections[0]
			if len(sections) > 0:
				res += sections[1:]

	for tidbit in res:
		if "=" not in tidbit:
			continue
		name = tidbit.split("=")[0].strip(" \r\n")
		value = "=".join(tidbit.split("=")[1:]).strip(" \r\n")
		print(name, value)
		if name == "alexa":
			sys.exit(0)

	print(json.dumps(res, indent=2))
	#sys.exit(0)

alexa_regex = re.compile(r"\|\s*alexa\s*=")

def handle_text(elem):
	if elem.text == None:
		return
	#if re.search(r'infobox\s*website', elem.text.lower()):
	#if "infobox" in elem.text.lower() and "alexa" in elem.text.lower():
	if "alexa" in elem.text and alexa_regex.search(elem.text) is not None:
		print(currentPage)
		sys.stdout.flush()
	#if "infobox" in elem.text.lower() and "website" in elem.text.lower():
		#d = min([len(s.split("website")) for s in elem.text.lower().split("infobox")])
		#if d < 100:
		#	print(currentPage)
	return
	if "infobox" not in elem.text:
		return
	return
	ast, _ = parse_text(elem.text)
	for part in ast:
		if isinstance(part, list):
			if not isinstance(part[1], list):
				if part[1].lower().startswith("infobox"):
					process_infobox(part)

start_events = {
	NS+"page": handle_start_page,
}

end_events = {
	NS+"title": handle_title,
	NS+"text": handle_text,
}

context = iter(ET.iterparse(sys.stdin, events=['start', 'end']))
_, root = next(context)
for event, elem in context:
	#print(elem.tag)
	if event == "start":
		if elem.tag in start_events:
			start_events[elem.tag](elem)
		pass
	elif event == "end":
		if elem.tag in end_events:
			end_events[elem.tag](elem)
		if elem.tag == NS+"page":
			root.clear()
		pass
