#!/usr/bin/env python
# -*- coding: utf8 -*-
"""Script for gathering GPW news.

Requires BeautifulSoup and requests:
$ pip install BeautifulSoup4
$ pip install requests
"""

from bs4 import BeautifulSoup
from subprocess import call

import codecs
import requests
import os

# biznesradar will be the source of news
BASE_URL = "http://www.biznesradar.pl/wiadomosci/"

# Name of the HTML file
FILE_NAME = "gpw.html"

# Add names of companies (taken from biznesradar website)
COMPANIES = [
    'BIOTON',
    'BSC-DRUKARNIA-OPAKOWAN',
    'ELEMENTAL-HOLDING',
    'RAWLPLUG',
    'TORPOL',
    'VISTULA',
    # 'SP-500'
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>GPW News</title>
        <script src="./js/jquery-1.12.0.min.js"></script>
        <script src="./js/jquery.dataTables.min.js"></script>
        <link rel="stylesheet" type="text/css" href="./css/jquery.dataTables.min.css">
    </head>
    <body>
        <table class="news" id="news" class="display" cellspacing="0" width="100%%">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Company</th>
                    <th>Source</th>
                    <th>Title</th>
                </tr>
            </thead>
            <tbody>
                %(content)s
            </tbody>
        </table>
        <!-- Add jQuery plugin for easy table manipulation -->
        <script type="text/javascript">
            $(document).ready(function() {
                $('#news').DataTable({
                    // Show 100 records by default
                    'iDisplayLength': 100,
                    // Order by first column (date) by default
                    "order": [[ 0, "desc" ]]
                    });
            } );
        </script>
    </body>
</html>
"""

NEWS_ELEMENT = """
<tr class="news_element">
    <td class="date">
        %(date)s
    </td>
    <td class="company">
        %(company)s
    </td>
    <td class="source">
        <img src="./images/%(source)s.png" alt="%(source)s">
    </td>
    <td class="title">
        <a href='%(title_url)s'>%(title_text)s</a>
    </td>
</tr>
"""


def generate_html_element(company, source, title_url, title_text, date):
    """Generate HTML for one element."""
    return NEWS_ELEMENT % {
        'company': company,
        'source': source,
        'title_url': title_url,
        'title_text': title_text,
        'title_text': title_text,
        'date': date
    }


def generate_html(news):
    """Generate whole HTML page."""
    return HTML_TEMPLATE % {'content': news}


def store_output(output):
    """Store output as HTML file."""
    with codecs.open('./gpw.html', 'w', 'utf-8') as output_file:
        output_file.write(output)


def main(verbose=False, open_in_browser=True):
    """Main function."""
    output = ""
    for company in COMPANIES:
        if verbose:
            print "Processing %s company" % company
        # Load the HTML
        page = requests.get(BASE_URL + company)
        # Page is not properly encoded
        page = page.text.encode('utf8')
        soup = BeautifulSoup(page, 'lxml')
        # News are in div#news-radar-body
        news = soup.findAll(class_="record-type-NEWS")
        for single_news in news:
            # Get the source
            image_tag = single_news.find('img')
            source = image_tag.attrs.get('alt', 'UNDEFINED')
            # Get the title - first link from the element
            title = single_news.find('a')
            title_text = title.text
            title_url = title.get('href')
            # Get the date of the news
            date_tag = single_news.find(class_='record-date')
            date = date_tag.text
            output += generate_html_element(company, source, title_url, title_text, date)
    html_output = generate_html(output)
    store_output(html_output)
    print "Finished"
    if open_in_browser:
        current_dir = os.getcwd()
        html_file = os.path.join(current_dir, FILE_NAME)
        call(["xdg-open", html_file])


if __name__ == "__main__":
    main()
