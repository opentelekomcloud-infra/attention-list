#!/usr/bin/python

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import re

from helper.utils import get_headers


class ZuulLister:
    """
    Base class which has all methods to create a list of failed Pull Requests
    from GitHub or Gitea repositories.
    """
    def __init__(self, config, args):
        self.config = config.get_config()
        self.args = args
    
    def check_config(self):
        if self.args.errors:
            if self.args.unknown_repos:
                raise Exception('Argument error: Zuul lister got more than '
                                'one argument: ' + self.args)
            if not self.config['zuul_list_errors']['url']:
                raise Exception('Configuration error: url missing for '
                                'zuul lister')
    
    def prepare_url(self, tenant):
        url = self.config['zuul_list_errors']['url']
        url = url + 'api/tenants/' + tenant + '/config-errors'
        
        return url

    def list_errors(self):
        data = []
        headers = {}
        headers['accept'] = 'application/json'
        tenants = self.config['zuul_list_errors']['tenants']
        for t in tenants:
            url = self.prepare_url(t)
            res = requests.request('GET', url=url, headers=headers)
            print(res)
            exit()

    
    def create_result(self, data):
        """
        Create dictionary result.
        """
        result = {}
        result['meta'] = {}
        result['data'] = []
        if data:
            result['data'] = data

        return result

    def list(self):
        self.check_config()
        if self.args.errors:
            return self.create_result(self.list_errors())
        elif self.args.unknown_repos:
            return self.create_result(['no repos found'])