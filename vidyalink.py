#! /usr/bin/env python

import sys
import irc.bot
import irc.strings
import re
import urllib
import requests
from BeautifulSoup import BeautifulSoup
import HTMLParser

URL_RE = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')

COLOR = u'\u0003'

def color_str(string, index):
    if sint(string[0]) == None:
        return COLOR+str(index)+string
    else:
        return COLOR+str(index)+' '+string

def sint(string):
    try:
        return int(string)
    except ValueError:
        return None

class VidyaBot(irc.bot.SingleServerIRCBot):
    muted = False
    owners = []

    def __init__(self, owners, channels, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)],
                                            nickname, nickname)
        self.joined_channels = channels
        self.owners = owners

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for chan in self.joined_channels:
            c.join(chan)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        message = e.arguments[0].strip()
        if message == "":
            return
        split_message = message.split(' ') 
        if split_message[0][0] == '@':
            self.do_command(e, split_message)
        elif not self.muted:
            self.parse_url(e, message)
        return

    def calculate_size(self, size):
        if sint(size) is None:
            return size
        exts = ['B', 'KB', 'MB', 'GB', 'TB'];
        counter = 0
        sz = int(size)
        sz = float(sz)
        while sz > 1024 and counter < len(exts):
            sz = float(int(sz/1024*100))/100
            counter = counter+1
        return str(sz)+exts[counter]


    def report_contents(self, headers):
        content_type = headers['content-type']
        if 'content-length' in headers:
            size = self.calculate_size(headers['content-length'])
            result = "Type: " + content_type + " | Size: " + size
        else:
            result = "Type: " + content_type
        return color_str(result, 3)

    def find_title(self, url):
        resp = requests.get(url)
        if resp.status_code != requests.codes.ok:
            return None
        soup = BeautifulSoup(resp.text)
        title = HTMLParser.HTMLParser().unescape(soup.html.head.title.string)
        return title


    def echo_url_stats(self, url):
        try:
            resp = requests.head(url)
        except requests.exceptions.ConnectionError as e:
            sys.stderr.write(e.message)
            return None
        if resp.status_code != requests.codes.ok:
            return None
        if "text/html" not in resp.headers["content-type"]:
            return url + " -> " + self.report_contents(resp.headers)
        else:
            return self.find_title(url)

    def parse_url(self, e, msg):
        for url in  URL_RE.findall(msg):
            stat = self.echo_url_stats(url[0])
            if stat is not None:
                self.connection.privmsg(e.target, stat)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        channel = e.target
        issuer = e.source.split('@')
        if len(issuer) == 1:
            return #no cloak
        sender = issuer[1].strip()

        if sender not in self.owners:
            return

        if cmd[0] == "@reconnect":
            if len(cmd) > 1:
                seconds = sint(cmd[1])
                if(seconds != None):
                    self.reconnection_interval = seconds
                    self.disconnect()
                    self.reconnection_interval = 60
                else:
                    self.disconnect()
        elif cmd[0] == "@die":
            self.die()
        elif cmd[0] == "@help":
            helpmsg = ("My commands are: @reconnect [seconds], @die, @mute, "
                      "@unmute and @help. Please don't use @die unless "
                      "necessary")
            self.connection.privmsg(channel, color_str(helpmsg,3))
        elif cmd[0] == "@mute":
            self.muted = True
        elif cmd[0] == "@unmute":
            self.muted = False
def main():
    server = "chat.freenode.net"
    port = 6667
    channels = ["#vidyadev", "##agdg"]
    owners = ["unaffiliated/morgawr", "unaffiliated/kuraitou"]
    bot = VidyaBot(owners, channels, "VidyaLink", server, port)
    bot.start()

if __name__ == "__main__":
    main()
