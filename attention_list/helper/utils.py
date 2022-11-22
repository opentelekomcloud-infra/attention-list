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
import requests


def create_result(items):
    """
    Create dictionary result list.
    """
    result = {}
    result['meta'] = {}
    result['data'] = []
    if len(items) != 0:
        items_json = []
        for obj in items:
            items_json.append(vars(obj))
        result['meta']['count'] = len(items_json)
        result['data'] = items_json
    else:
        result['meta']['count'] = 0

    return result


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
    if hoster == 'gitea':
        headers['Authorization'] = 'token ' + get_token(
            hoster=hoster,
            args=args
        )
    elif hoster == 'github':
        headers['Authorization'] = 'Bearer ' + get_token(
            hoster=hoster,
            args=args
        )
    else:
        raise Exception('No hoster found in get_headers().')

    return headers


def get_pull_requests(hoster, url, headers, org, repo, state=None):
    """
    Collect all open Pull Requests of a Git Repository
    """
    pullrequests = []

    if hoster == 'gitea':
        req_url = (
            url
            + 'repos/'
            + org
            + '/'
            + repo
            + '/pulls')
        if state:
            req_url = req_url + '?state=' + state
        try:
            res = requests.request('GET', url=req_url, headers=headers)
            if res.json():
                for pr in res.json():
                    pullrequests.append(pr)
        except Exception as e:
            print("get_pull_requests error: " + str(e))
            print(
                "The request status is: "
                + str(res.status_code)
                + " | "
                + str(res.reason))
            exit()
    elif hoster == 'github':
        i = 1
        while True:
            try:
                req_url = (
                    url
                    + 'repos/'
                    + org
                    + '/'
                    + repo
                    + '/pulls?page='
                    + str(i))
                if state:
                    req_url = req_url + '&state=' + state
                res = requests.request('GET', url=req_url, headers=headers)
                if res.json():
                    for pr in res.json():
                        pullrequests.append(pr)
                    i += 1
                    continue
                else:
                    break
            except Exception as e:
                print("Get GitHub pullrequests error: " + str(e))
                print(
                    "The request status is: "
                    + str(res.status_code)
                    + " | "
                    + str(res.reason))
                exit()
    return pullrequests


def get_repos(hoster, url, headers, org):
    """
    Get all Repositories of a Git organization
    """
    repositories = []

    if hoster == 'gitea':
        i = 1
        while True:
            try:
                req_url = (
                    url
                    + 'orgs/'
                    + org
                    + '/repos?limit=50&page='
                    + str(i))
                res = requests.request('GET', url=req_url, headers=headers)
                i += 1
                if res.json():
                    for repo in res.json():
                        repositories.append(repo['name'])
                    continue
                else:
                    break
            except Exception as e:
                print("Get Gitea Repos error: " + str(e))
                print(
                    "The request status is: "
                    + str(res.status_code)
                    + " | "
                    + str(res.reason))
                break
    elif hoster == 'github':
        i = 1
        while True:
            try:
                req_url = (
                    url
                    + 'orgs/'
                    + org
                    + '/repos?page='
                    + str(i))
                res = requests.request('GET', url=req_url, headers=headers)
                if res.json():
                    for repo in res.json():
                        if repo['archived'] is False:
                            repositories.append(repo['name'])
                    i += 1
                    continue
                else:
                    break
            except Exception as e:
                print("Get Github repository error: " + str(e))
                print(
                    "The request status is: "
                    + str(res.status_code)
                    + " | "
                    + str(res.reason))
                break
    return repositories
