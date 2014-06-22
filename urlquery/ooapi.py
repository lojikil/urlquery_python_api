#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json

import requests
from dateutil.parser import parse
from datetime import datetime, timedelta
import time


base_url = 'https://uqapi.net/v3/json'
gzip_default = False


class URLQuery(object):
    __slots__ = ["_feed_type", "_intervals", "_priorities", "_search_types",
                 "_result_types", "_url_types", "gzip_default", "base_url",
                 "_url_matchings", "apikey"]

    def __init__(self, base_url=None, gzip_default=False, apikey=None):
        self._feed_type = ['unfiltered', 'flagged']
        self._intervals = ['hour', 'day']
        self._priorities = ['urlfeed', 'low', 'medium', 'high']
        self._search_types = ['string', 'regexp', 'ids_alert',
                              'urlquery_alert', 'js_script_hash']
        self._result_types = ['reports', 'url_list']
        self._url_matchings = ['url_host', 'url_path']
        self.gzip_default = gzip_default

        if base_url is not None:
            self.base_url = base_url
        else:
            self.base_url = 'https://uqapi.net/v3/json'

        if apikey is not None:
            self.apikey = apikey
        else:
            self.apikey = ''

    def query(self, query, gzip=False, apikey=None):
        if query.get('error') is not None:
            return query

        if self.gzip_default or gzip:
            query['gzip'] = True

        if apikey is not None:
            query['key'] = apikey
        else:
            query['key'] = self.apikey

        r = requests.post(base_url, data=json.dumps(query))
        return r.json()

    def urlfeed(self, feed='unfiltered', interval='hour', timestamp=None,
                gzip=False, apikey=None):
        """
            The urlfeed function is used to access the main feed of URL from
            the service. Currently there are two distinct feed:


                :param feed: Currently there are two distinct feed:

                    * *unfiltered*: contains all URL received by the service,
                        as with other API calls some restrictions to the feed
                        might apply depending. (default)
                    * *flagged*: contains URLs flagged by some detection by
                        urlquery, it will not contain data triggered by IDS
                        alerts as that not possible to correlate correctly to a
                        given URL. Access to this is currently restricted.

                :param interval: Sets the size of time window.
                        * *hour*: splits the day into 24 slices which each
                            goes from 00-59 of every hour,
                            for example: 10:00-10:59 (default)
                        * *day*: will return all URLs from a given date

                :param timestamp: This selects which slice to return.
                                  Any timestamp within a given interval/time
                                  slice can be used to return URLs from that
                                  timeframe. (default: now)


                :return: URLFEED

                    {
                        "start_time" : string,
                        "end_time"   : string,
                        "feed"       : [URLs]    Array of URL objects
                    }

                For more information on "feed", please see the README

        """
        query = {'method': 'urlfeed'}
        if feed not in self._feed_type:
            query.update({'error':
                          'Feed can only be in ' +
                          ', '.join(self._feed_type)})
        if interval not in self._intervals:
            query.update({'error':
                          'Interval can only be in ' +
                          ', '.join(self._intervals)})
        if timestamp is None:
            ts = datetime.now()
            if interval == 'hour':
                ts = ts - timedelta(hours=1)
            if interval == 'day':
                ts = ts - timedelta(days=1)
            timestamp = time.mktime(ts.utctimetuple())
        else:
            try:
                timestamp = time.mktime(parse(timestamp).utctimetuple())
            except:
                query.update({'error':
                              'Unable to convert time to timestamp: ' +
                              str(time)})
        query['feed'] = feed
        query['interval'] = interval
        query['timestamp'] = timestamp
        return self.query(query, gzip, apikey)

    def submit(self, url, useragent=None, referer=None, priority='low',
               access_level='public', callback_url=None, submit_vt=False,
               save_only_alerted=False, gzip=False, apikey=None):
        """
            Submits an URL for analysis.

            :param url: URL to submit for analysis

            :param useragent: See user_agent_list API function. Setting an
                invalid UserAgent will result in a random UserAgent getting
                selected.

            :param referer: Referer to be applied to the first visiting URL

            :param priority: Set a priority on the submission.
                * *urlfeed*: URL might take several hour before completing.
                    Used for big unfiltered feeds. Some filtering applies
                    before accepting to queue so a submitted URL might not
                    be tested.
                * *low*: For vetted or filtered feeds (default)
                * *medium*: Normal submissions
                * *high*: To ensure highest priority.

            :param access_level: Set accessibility of the report
                * *public*: URL is publicly available on the site (default)
                * *nonpublic*: Shared with other security organizations or
                               researchers.
                * *private*: Only submitting key has access.

            :param callback_url: Results are POSTed back to the provided
                URL when processing has completed. The results will be
                originating from uqapi.net. Requires an API key.

            :param submit_vt: Submits any unknown file toVirusTotal for
                analysis. Information from VirusTotal will be included the
                report as soon as they have finished processing the sample.
                Most likely will the report from urlquery be available
                before the data is received back from VirusTotal.
                Default: false

                Only executables, zip archives and pdf documents are
                currently submitted.

                .. note:: Not fully implemented yet.

            :param save_only_alerted: Only reports which contains alerts
                (IDS, UQ alerts, Blacklists etc.) are kept. The main purpose
                for this flag is for mass testing URLs which has not been
                properly vetted so only URLs of interest are kept.
                Default: false

                Combining this with a callback URL will result in only those
                that has alerts on them beingPOSTed back to the callback URL.

            :return: QUEUE_STATUS

                {
                    "status"     : string,  ("queued", "processing", "done")
                    "queue_id"   : string,
                    "report_id"  : string,   Included once "status" = "done"
                    "priority"   : string,
                    "url"        : URL object,      See README
                    "settings"   : SETTINGS object  See README
                }


        """
        query = {'method': 'submit'}
        if priority not in self._priorities:
            query.update({'error':
                          'priority must be in ' +
                          ', '.join(self._priorities)})
        if access_level not in self._access_levels:
            query.update({'error':
                          'assess_level must be in '
                          + ', '.join(self._access_levels)})
        query['url'] = url
        if useragent is not None:
            query['useragent'] = useragent
        if referer is not None:
            query['referer'] = referer
        query['priority'] = priority
        query['access_level'] = access_level
        if callback_url is not None:
            query['callback_url'] = callback_url
        if submit_vt:
            query['submit_vt'] = True
        if save_only_alerted:
            query['save_only_alerted'] = True
        return self.query(query, gzip, apikey)

    def user_agent_list(self, gzip=False, apikey=None):
        """
            Returns a list of accepted user agent strings. These might
            change over time, select one from the returned list.

            :return: A list of accepted user agents
        """
        query = {'method': 'user_agent_list'}
        return self.query(query, gzip, apikey)

    def mass_submit(self, urls, useragent=None, referer=None,
                    access_level='public', priority='low', callback_url=None,
                    gzip=False, apikey=None):
        """
            See submit for details. All URLs will be queued with the same
            settings.

            :return:

                {
                    [QUEUE_STATUS]  Array of QUEUE_STATUS objects, See submit
                }
        """
        query = {'method': 'mass_submit'}
        if access_level not in self._access_levels:
            query.update({'error':
                          'assess_level must be in ' +
                          ', '.join(self._access_levels)})
        if priority not in self._priorities:
            query.update({'error': 'priority must be in ' +
                          ', '.join(self._priorities)})
        if useragent is not None:
            query['useragent'] = useragent
        if referer is not None:
            query['referer'] = referer
        query['access_level'] = access_level
        query['priority'] = priority
        if callback_url is not None:
            query['callback_url'] = callback_url
        return self.query(query, gzip, apikey)

    def queue_status(self, queue_id, gzip=False, apikey=None):
        """
            Polls the current status of a queued URL. Normal processing time
            for a URL is about 1 minute.

            :param queue_id: QueueIDis returned by the submit API calls

            :return: QUEUE_STATUS (See submit)
        """
        query = {'method': 'queue_status'}
        query['queue_id'] = queue_id
        return self.query(query, gzip=False, apikey=None)

    def report(self, report_id, recent_limit=0, include_details=False,
               include_screenshot=False, include_domain_graph=False,
               gzip=False, apikey=None):
        """
            This extracts data for a given report, the amount of data and
            what is included is dependent on the parameters set and the
            permissions of the API key.

            :param report_id: ID of the report. To get a valid report_id
                either use search to look for specificreports or report_list
                to get a list of recently finished reports.
                Can be string or an integer

            :param recent_limit: Number of recent reports to include.
                Only applies when include_details is true.
                Integer, default: 0

            :param include_details: Includes details in the report, like the
                alert information, Javascript and transaction data.
                Default: False

            :param include_screenshot: A screenshot is included in the report
                as a base64. The mime type of the image is also included.
                Default: False

            :param include_domain_graph: A domain graph is included in the
                report as a base64. The mime type of the image is also
                included.
                Default: False


            :return: BASICREPORT

                {
                    "report_id": string,
                    "date"     : string,    Date formatted string
                    "url"      : URL,       URL object      - See README
                    "settings" : SETTINGS,  SETTINGS object - See README
                    "urlquery_alert_count"  : int,  Total UQ alerts
                    "ids_alert_count"       : int,  Total IDS alert
                    "blacklist_alert_count" : int,  Total Blacklist alerts
                    "screenshot"    : BINBLOB,      BINBLOB object - See README
                    "domain_graph"  : BINBLOB       BINBLOB object - See README
                }
        """
        query = {'method': 'report'}
        query['report_id'] = report_id
        if recent_limit is not None:
            query['recent_limit'] = recent_limit
        if include_details:
            query['include_details'] = True
        if include_screenshot:
            query['include_screenshot'] = True
        if include_domain_graph:
            query['include_domain_graph'] = True
        return self.query(query, gzip, apikey)

    def report_list(self, timestamp=None, limit=50, gzip=False, apikey=None):
        """
        Returns a list of reports created from the given timestamp, if it’s
        not included the most recent reports will be returned.

        Used to get a list of reports from given timestamp, along with basic
        information about the report like number of alerts and the
        submitted URL.

        To get reports which are nonpublic or private a API key is needed
        which has access to these.

        :param timestamp: Unix Epoch timestamp from the starting point to get
            reports.
            Default: If None, setted to datetime.now()

        :param limit: Number of reports in the list
            Default: 50

        :return:

            {
                "reports": [BASICREPORTS]   List of BASICREPORTS - See report
            }

        """
        query = {'method': 'report_list'}
        if timestamp is None:
            ts = datetime.now()
            timestamp = time.mktime(ts.utctimetuple())
        else:
            try:
                timestamp = time.mktime(parse(timestamp).utctimetuple())
            except:
                query.update({'error':
                              'Unable to convert time to timestamp: ' +
                              str(time)})
        query['timestamp'] = timestamp
        query['limit'] = limit
        return self.query(query, gzip, apikey)

    def search(q, search_type='string', result_type='reports',
               url_matching='url_host', date_from=None, deep=False,
               gzip=False, apikey=None):
        """
            Search in the database

            :param q: Search query

            :param search_type: Search type
                * *string*: Used to find URLs which contains a given string.
                    To search for URLs on a specific IP use string. If a
                    string is found to match an IP address it will automaticly
                    search based on the IP. (default)
                * *regexp*: Search for a regexp pattern within URLs
                * *ids_alert*: Search for specific IDS alerts
                * *urlquery_alert*: ????? FIXME ?????
                * *js_script_hash*: Used to search for URLs/reports which
                    contains a specific JavaScript. The scripts are searched
                    based on SHA256, the hash value for each script are
                    included in the report details. Can be used to find other

            :param result_type: Result type
                * *reports*: Full reports (default)
                * *url_list*: List of urls

            :param url_matching: What part of an URL to do pattern matching
                against. Only applies to string and regexp searches.
                * *url_host*: match against host (default)
                * *url_path*: match against path


            :param date_from: Unix epoch timestamp for starting search point.
                Default: If None, setted to datetime.now()


            :param deep: Search all URLs, not just submitted URLs.
                Default: false
                Experimental! Should be used with care as it’s very resource
                intensive.
        """
        query = {'method': 'search'}
        if search_type not in self._search_types:
            query.update({'error':
                          'search_type can only be in '
                          + ', '.join(self._search_types)})
        if result_type not in self._result_types:
            query.update({'error':
                          'result_type can only be in '
                          + ', '.join(self._result_types)})
        if url_matching not in self._url_matchings:
            query.update({'error':
                          'url_matching can only be in '
                          + ', '.join(self._url_matchings)})

        if date_from is None:
            ts = datetime.now()
            timestamp = time.mktime(ts.utctimetuple())
        else:
            try:
                timestamp = time.mktime(parse(date_from).utctimetuple())
            except:
                query.update({'error':
                              'Unable to convert time to timestamp: '
                              + str(time)})

        query['q'] = q
        query['search_type'] = search_type
        query['result_type'] = result_type
        query['url_matching'] = url_matching
        query['from'] = timestamp
        if deep:
            query['deep'] = True
        return self.query(query, gzip, apikey)

    def reputation(self, q, gzip=False, apikey=None):
        """
            Searches a reputation list of URLs detected over the last month.
            The search query can be a domain or an IP.

            With an API key, matching URLs will be returned along with the
            triggering alert.

            :param q: Search query
        """

        query = {'method': 'reputation'}
        query['q'] = q
        return self.query(query, gzip, apikey)
