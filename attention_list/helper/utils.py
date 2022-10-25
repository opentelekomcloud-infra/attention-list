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

import os

def get_token(hoster, args):
    token = ''
    if hoster == 'github':
        if args.github_token:
            token = args.github_token
        elif os.getenv('GITHUB_TOKEN'):
            token = os.getenv('GITHUB_TOKEN')
        else:
            raise Exception(
                'Please, provide GitHub Token as console argument or \n'
                'as environment variable GITHUB_TOKEN')
    elif hoster == 'gitea':
        if args.gitea_token:
            token = args.gitea_token
        elif os.getenv('GITEA_TOKEN'):
            token = os.getenv('GITEA_TOKEN')
        else:
            raise Exception(
                'Please, provide Gitea Token as console argument or \n'
                'as environment variable GITEA_TOKEN')
    else:
        raise ValueError('No supported Git hoster provided.')
    return token

def get_headers(hoster, args):
    headers = {}
    headers['accept'] = 'application/json'
    headers['Authorization'] = 'token ' + get_token(
        hoster=hoster,
        args=args
    )

    return headers