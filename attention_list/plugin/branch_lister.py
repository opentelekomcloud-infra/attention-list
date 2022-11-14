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
from helper.utils import create_result

git_hoster = ['gitea', 'github']


class EmptyBranch:
    """Branch without any open Pull Request"""
    def __init__(
            self,
            org=None,
            repo=None,
            hoster=None,
            name=None):

        self.org = org
        self.repo = repo
        self.hoster = hoster
        self.name = name


class BranchLister:
    """
    Base class which has all methods to create a list Branches with to be
    defined
    from GitHub or Gitea repositories.
    """
    def __init__(self, config, args):
        self.config = config.get_config()
        self.args = args

    def print_config(self):
        print(self.config)

    def check_config(self):
        if not self.config['branch_list_empty']['git_hoster']:
            raise Exception('Config missing git_hoster entry.')
        hoster = self.config['branch_list_empty']['git_hoster']
        for h in hoster:
            if h['name'] not in git_hoster:
                raise Exception('git_hoster[\'name\'] wrong: ' + h['name'])
            if not h['api_url']:
                raise Exception('git_hoster[\'api_url\'] missing '
                                'for git_hoster: ' + h['name'])
            if (not h['orgs']) or (not isinstance(h['orgs'], list)):
                raise Exception('git_hoster[\'orgs\'] missing '
                                'or not type of list for git_hoster: '
                                + h['name'])

    def get_gitea_repos(self, url, headers, gitea_org):
        """
        Get all Repositories of one Gitea orgainzation
        """
        repositories = []
        i = 1
        while True:
            try:
                req_url = (
                    url
                    + 'orgs/'
                    + gitea_org
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
        return repositories

    def get_gitea_branches(self, url, headers, gitea_org, repo):
        """
        Collect all branches of a Gitea Repository
        """
        branches = []

        try:
            req_url = (
                url
                + 'repos/'
                + gitea_org
                + '/'
                + repo
                + '/branches')
            res = requests.request('GET', url=req_url, headers=headers)
            if res.json():
                branches_raw = res.json()
                for branch in branches_raw:
                    if branch['name'] and (branch['name'] != 'main'):
                        branches.append(branch['name'])
        except Exception as e:
            print("get_gitea_branches error: " + str(e))
            print(
                "The request status is: "
                + str(res.status_code)
                + " | "
                + str(res.reason))
            exit()
        return branches

    def get_gitea_prs(self, url, headers, gitea_org, repo):
        """
        Collect all Pull Requests of a Gitea Repository
        """
        pullrequests = []

        try:
            req_url = (
                url
                + 'repos/'
                + gitea_org
                + '/'
                + repo
                + '/pulls?state=open')
            res = requests.request('GET', url=req_url, headers=headers)
            if res.json():
                for pr in res.json():
                    pullrequests.append(pr)
        except Exception as e:
            print("get_gitea_branches error: " + str(e))
            print(
                "The request status is: "
                + str(res.status_code)
                + " | "
                + str(res.reason))
            exit()
        return pullrequests

    def get_github_repos(self, url, headers, github_org):
        """
        Get all repositories of one GitHub organization
        """
        repositories = []
        i = 1

        while True:
            try:
                req_url = url + 'orgs/' + github_org + '/repos?page=' + str(i)
                res = requests.request('GET', url=req_url, headers=headers)
                if res.json():
                    for repo in res.json():
                        print(repo)
                        exit()
                        if repo['archived'] is False:
                            repositories.append(repo)
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

    def get_github_prs(self, url, headers, github_org, repo):
        """
        Get all Pull Requests of one GitHub repository
        """
        pullrequests = []
        i = 1

        while True:
            try:
                req_url = (
                    url
                    + 'repos/'
                    + github_org
                    + '/'
                    + repo
                    + '/pulls?state=open&page='
                    + str(i))
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
                break
        return pullrequests

    def get_gitea_branches_with_pr(self, pulls):
        branches = []
        for pr in pulls:
            branch_base = pr['base']['repo']['full_name']
            branch_head = pr['head']['repo']['full_name']
            if branch_base == branch_head:
                branches.append(pr['head']['ref'])
        return branches

    def get_empty_branches(self, hoster, org, repo, pulls, branches):
        empty_branches = branches
        full_branches = self.get_gitea_branches_with_pr(
            pulls=pulls)
        for b in full_branches:
            empty_branches.remove(b)
        result = self.create_obj_branches(
            hoster=hoster,
            org=org,
            repo=repo,
            branches=empty_branches
        )

        return result

    def create_obj_branches(self, hoster, org, repo, branches):
        result = []
        for b in branches:
            item = EmptyBranch(
                hoster=hoster,
                org=org,
                repo=repo,
                name=b
            )
            result.append(item)
        return result

    def list_empty(self):
        """
        Method to run through every repository in each organization of one
        or more Git providers to collect all Branches having no open
        Pull Requests left and could be closed.
        """
        self.check_config()
        self.hoster = self.config['branch_list_empty']['git_hoster']

        empty_branches = []
        for h in self.hoster:
            if h['name'] == 'gitea':
                headers = get_headers(
                    hoster=h['name'],
                    args=self.args
                )
                for org in h['orgs']:
                    repos = []
                    if h['repos']:
                        repos = h['repos']
                    else:
                        repos = self.get_gitea_repos(
                            url=h['api_url'],
                            headers=headers,
                            gitea_org=org
                        )
                    for repo in repos:
                        branches = self.get_gitea_branches(
                            url=h['api_url'],
                            headers=headers,
                            gitea_org=org,
                            repo=repo
                        )
                        pulls = self.get_gitea_prs(
                            url=h['api_url'],
                            headers=headers,
                            gitea_org=org,
                            repo=repo
                        )
                        if branches:
                            result_branches = self.get_empty_branches(
                                hoster=h['name'],
                                org=org,
                                repo=repo,
                                pulls=pulls,
                                branches=branches)
                            empty_branches.extend(result_branches)

            # elif h['name'] == 'github':
            #     headers = get_headers(
            #         hoster=h['name'],
            #         args=self.args
            #     )
            #     for org in h['orgs']:
            #         repos = self.get_github_repos(
            #             url=h['api_url'],
            #             headers=headers,
            #             github_org=org
            #         )
            #         for repo in repos:
            #             pulls = self.get_github_prs(
            #                 url=h['api_url'],
            #                 headers=headers,
            #                 github_org=org,
            #                 repo=repo['name']
            #             )
            #             if pulls:
            #                 for pull in pulls:
            #                     commits = self.get_github_failed_commits(
            #                         pull=pull,
            #                         url=h['api_url'],
            #                         github_org=org,
            #                         repo=repo,
            #                         headers=headers
            #                     )
            #                     failed_commits.extend(commits)

        return create_result(empty_branches)