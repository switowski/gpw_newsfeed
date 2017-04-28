#!/usr/bin/env python
# -*- coding: utf8 -*-
"""Script for gathering GPW news.

Requires BeautifulSoup and requests:
$ pip install BeautifulSoup4
$ pip install requests
"""

from bs4 import BeautifulSoup
from subprocess import call

import argparse
import codecs
import datetime
import requests
import os

# we use biznesradar as a source website
BASE_URL = "http://www.biznesradar.pl/"
NEWS_URL = "http://www.biznesradar.pl/wiadomosci/"
AT_URL = "http://www.biznesradar.pl/notowania/"

# Name of the HTML file
FILE_NAME = "gpw.html"

# Add names of companies (taken from biznesradar website)
COMPANIES = [
    'BSC-DRUKARNIA-OPAKOWAN',
    'ELEMENTAL-HOLDING',
    'ERG',
    'FERRO',
    'FORTE',
    'INTER-CARS',
    'JSW-JASTRZEBSKA-SPOLKA-WEGLOWA',
    'LIVECHAT',
    'LSI-SOFTWARE',
    'MARVIPOL',
    'MERCATOR',
    'MONNARI-TRADE',
    'PEPEES',
    'RAWLPLUG',
    'ROBYG',
    'VISTULA',
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>GPW News</title>
        <script src="./js/jquery-1.12.0.min.js"></script>
        <script src="./js/jquery.dataTables.min.js"></script>
        <script src="./js/dataTables.bootstrap.min.js"></script>
        <link rel="stylesheet" type="text/css" href="./css/bootstrap.min.css">
        <link rel="stylesheet" type="text/css" href="./css/dataTables.bootstrap.min.css">
        <link rel="stylesheet" type="text/css" href="./css/styles.css">
    </head>
    <body>
        <div class="container">
            <div>
                <h2>News</h2>
                <table id="news" class="news table table-striped table-bordered" cellspacing="0" width="100%%">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Company</th>
                            <th>Source</th>
                            <th>Title</th>
                        </tr>
                    </thead>
                    <tbody>
                        %(news)s
                    </tbody>
                </table>
            </div>
            <div>
                <h2>AT</h2>
                <table id="at" class="at table table-striped table-bordered" cellspacing="0" width="100%%">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Company</th>
                            <th>What</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        %(at)s
                    </tbody>
                </table>
            </div>
        </div>
        <!-- Add jQuery plugin for easy table manipulation -->
        <script type="text/javascript">
            $(document).ready(function() {
                $('#news').DataTable({
                    // Uncomment to show 100 records by default
                    // 'iDisplayLength': 100,
                    // Order by first column (date) by default
                    "order": [[ 0, "desc" ]]
                    });
                $('#at').DataTable({
                    // show 100 records by default
                    'iDisplayLength': 50,
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

AT_ELEMENT = """
<tr class="at_element">
    <td class="date">
        %(date)s
    </td>
    <td class="company">
        %(company)s
    </td>
    <td class="title %(direction)s">
        <a href='%(url)s'>%(text)s</a>
    </td>
    <td class="at_type">
        %(at_type)s
    </td>
</tr>
"""


MONTHS = {
    'sty': '01',
    'lut': '02',
    'mar': '03',
    'kwi': '04',
    'maj': '05',
    'cze': '06',
    'lip': '07',
    'sie': '08',
    'wrz': '09',
    'pa\xc5\xba': '10',
    'lis': '11',
    'gru': '12',
}

def parse_date(date):
    """Gets the ugly and random data format from the website and returns
    normalized data
    """
    now = datetime.date.today()
    current_year = datetime.date.today().year

    parts = date.split()
    if len(parts) == 1:
        # This situation shouldn't happen. Data has at least 2 parts
        return 'ERROR'
    elif len(parts) >= 2:
        day = int(parts[0])
        month = int(MONTHS.get(parts[1].encode('utf-8'), 'ERROR'))
        year = current_year
        # Get the year - if the day and month from the date + current year is
        # in the future from now, it means the year in the date is last year
        if datetime.date(year, month, day) > now:
            year = year- 1
    try:
        time = parts[2]
    except IndexError:
        # There was no time, use default time
        time = '00:00'
    return "%s-%02d-%02d %s" % (year, month, day, time)


def generate_news_element(company, source, title_url, title_text, date):
    """Generate HTML for one element."""
    return NEWS_ELEMENT % {
        'company': company,
        'source': source,
        'title_url': title_url,
        'title_text': title_text,
        'title_text': title_text,
        'date': date
    }

def generate_at_element(company, direction, url, text, date, at_type):
    """Generate HTML for one element."""
    return AT_ELEMENT % {
        'company': company,
        'direction': direction,
        'url': url,
        'text': text,
        'date': date,
        'at_type': at_type
    }


def generate_html(news, at):
    """Generate whole HTML page."""
    return HTML_TEMPLATE % {'news': news,
                            'at': at }

def store_output(output):
    """Store output as HTML file."""
    with codecs.open('./gpw.html', 'w', 'utf-8') as output_file:
        output_file.write(output)


def main(verbose=False, open_in_browser=True):
    """Main function."""
    news_output = ""
    # AT contains both candles and signals
    at = ""
    for company in COMPANIES:
        if verbose:
            print "Processing %s company" % company
        # GET NEWS FOR COMPANY
        # Load the HTML
        page = requests.get(NEWS_URL + company)
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
            news_output += generate_news_element(company, source, title_url, title_text, date)

        # GET TECHNICAL ANALYSIS
        # Load the HTML
        page = requests.get(AT_URL + company)
        # Page is not properly encoded
        page = page.text.encode('utf8')
        soup = BeautifulSoup(page, 'lxml')
        # From here, get the "formacje swiecowe" and "sygnaly AT"
        candles_element = soup.find(id="profile-candlesticks")
        candles = candles_element.findAll('tr')
        for candle in candles:
            candle_name_class = candle.find('td', class_='name').attrs.get('class', ['name'])
            candle_link = candle.find('td', class_='name').find('a')
            url = BASE_URL + candle_link.attrs.get('href', '#')
            text = candle_link.attrs.get('title', 'Error')
            if text == 'Error':
                raise 'ups'
            date = candle.find('td', class_='value').text
            # Normalize date
            date = parse_date(date)
            # candle_name_class should now contain only 'name' and down/up
            # After we call 'remove' it's removed from the DOM object, so
            # this has to be the last action
            candle_name_class.remove('name')
            direction = candle_name_class[0]
            at_type = 'Candle'

            at += generate_at_element(company, direction, url, text, date, at_type)

        signals_element = soup.find(id="profile-signals")
        signals = signals_element.findAll('tr')
        for signal in signals:
            signal_name_class = signal.find('td', class_='name').attrs.get('class', ['name'])
            signal_link = signal.find('td', class_='name').find('a')
            url = BASE_URL + signal_link.attrs.get('href', '#')
            text = signal_link.text
            if text == 'Error':
                raise 'ups'
            date = signal.find('td', class_='value').text
            # Normalize date
            date = parse_date(date)
            # candle_name_class should now contain only 'name' and down/up
            signal_name_class.remove('name')
            direction = signal_name_class[0]
            at_type = 'Signal'

            at += generate_at_element(company, direction, url, text, date, at_type)

    html_output = generate_html(news_output, at)
    store_output(html_output)
    print "Finished"
    if open_in_browser:
        current_dir = os.getcwd()
        html_file = os.path.join(current_dir, FILE_NAME)
        call(["xdg-open", html_file])


if __name__ == "__main__":
    main()
