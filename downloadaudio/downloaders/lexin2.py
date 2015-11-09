# -*- mode: python; coding: utf-8 -*-

import urllib2
import json
from BeautifulSoup import BeautifulSoup

from .downloader import AudioDownloader
from ..download_entry import DownloadEntry


class LexinDownloader2(AudioDownloader):
    def __init__(self):
        AudioDownloader.__init__(self)
        self.icon_url = 'http://lexin.nada.kth.se/lexin/'
        self.url = 'http://lexin.nada.kth.se/sound/'

    def download_files(self, field_data):
        """Get pronunciations of a word in Swedish from Lexin"""
        self.downloads_list = []
        if not self.language.lower().startswith('sv'):
            return
        if field_data.split:
            return
        if not field_data.word:
            return
        # These headers are necessary
        # Without them, the server returns 500 response
        headers = {
            'Content-Type': 'text/x-gwt-rpc; charset=utf-8',
            'X-GWT-Permutation': 'B3637EFE47DBD18879B4B4582D033CEA'}
        # GWT-RPC encoded payload string
        payload = (
            '7|0|7|http://lexin.nada.kth.se/lexin/lexin/|'
            'FCDCCA88916BAACF8B03FB48D294BA89|'
            'se.jojoman.lexin.lexingwt.client.LookUpService|'
            'lookUpWord|se.jojoman.lexin.lexingwt.client.LookUpRequest/682723451|swe_swe|' +
            field_data.word.encode('utf-8') + '|1|2|3|4|1|5|5|1|6|1|7|')
        request = urllib2.Request(
            'http://lexin.nada.kth.se/lexin/lexin/lookupword',
            payload, headers)
        response = urllib2.urlopen(request)
        # Check that response code is 200 (OK)
        if 200 != response.code:
            raise ValueError(str(response.code) + ': ' + response.msg)
        # Strip leading '//OK' and
        # exchange invalid hex escapes with unicode escapes
        data = response.read()[4:].replace('\\x', '\\u00')
        # data is now a valid json list.
        # Each word has a corresponding xml string
        # inside the list.
        word_xmls = json.loads(data)[-3][3:-2]
        if word_xmls:
            self.maybe_get_icon()
        for word_xml in word_xmls:
            soup = BeautifulSoup(word_xml)
            extras = dict(Source='Lexin')
            try:
                extras['Type'] = soup.find('lemma')['type']
            except AttributeError:
                pass
            try:
                audio_link = self.url + soup.find('phonetic')['file']
                entry = DownloadEntry(
                    field_data,
                    self.get_tempfile_from_url(audio_link),
                    extras,
                    self.site_icon)
            except:
                continue
            try:
                entry.word = soup.find('lemma')['value']
            except AttributeError:
                pass
            self.downloads_list.append(entry)
