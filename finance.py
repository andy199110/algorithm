# -*- coding:utf-8 -*-
import re

__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()
from bs4 import BeautifulSoup
import urllib2
import webbrowser
webbrowser.open('https://docs.python.org/2/library/webbrowser.html')
url = 'http://www.eastmoney.com/'
request = urllib2.Request(url)
response = urllib2.urlopen(request, timeout=20)

content = response.read()
soup = BeautifulSoup(content, 'html.parser')
page=soup.find_all(string=re.compile("http://finance.eastmoney.com/news/"))
print page
s=0




start_quote = page.find('"http', s)
end_quote = page.find('"', start_quote + 1)
url = page[start_quote + 1:end_quote]
print url


