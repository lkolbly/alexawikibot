Wiki Alexa Updater
==================

This is a short script to automatically update alexa rankings of website infoboxes on Wikipedia.

Use at your own risk!

find_potential_alexas.py is a short script to quickly (~1hr) scrape a XML dump (fed through stdin) for articles that are potential candidates for being updated. (i.e. they have website infoboxes)

alexa.py consumes that candidate list and uses pywikibot and myawis to generate the new alexa data.
