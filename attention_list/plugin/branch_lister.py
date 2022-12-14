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

from attention_list.helper.utils import check_config
from attention_list.helper.utils import create_result
from attention_list.helper.utils import get_headers
from attention_list.helper.utils import get_pull_requests
from attention_list.helper.utils import get_repos


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

    def get_branches(self, url, headers, org, repo):
        """
        Collect all branches of a Git Repository
        """
        branches = []
        try:
            req_url = (
                url
                + 'repos/'
                + org
                + '/'
                + repo
                + '/branches')
            res = requests.request('GET', url=req_url, headers=headers)
        except Exception as e:
            print("get_branches error: " + str(e))
            print(
                "The request status is: "
                + str(res.status_code)
                + " | "
                + str(res.reason))
            exit()

        if res.json():
            branches_raw = res.json()
            for branch in branches_raw:
                if branch['name']:
                    if branch['name'] != 'main' and \
                            branch['name'] != 'master':
                        branches.append(branch['name'])
        return branches

    def get_branches_with_pr(self, pulls):
        branches = []
        for pr in pulls:
            branch_base = pr['base']['repo']['full_name']
            branch_head = pr['head']['repo']['full_name']
            if branch_base == branch_head:
                branches.append(pr['head']['ref'])
        return branches

    def get_empty_branches(self, hoster, org, repo, pulls, branches):
        empty_branches = branches
        full_branches = []
        full_branches = self.get_branches_with_pr(pulls=pulls)
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
        command: branch list empty

        Method to run through every repository in each organization of one
        or more Git providers to collect all Branches having no open
        Pull Requests left and could be closed.
        """
        check_config(
            command='branch_list_empty',
            config=self.config
        )
        self.hoster = self.config['branch_list_empty']['git_hoster']

        empty_branches = []
        for h in self.hoster:
            if h['name'] == 'gitea' or h['name'] == 'github':
                headers = get_headers(
                    hoster=h['name'],
                    args=self.args
                )
                for org in h['orgs']:
                    repos = []
                    if h['repos']:
                        repos = h['repos']
                    else:
                        repos = get_repos(
                            hoster=h['name'],
                            url=h['api_url'],
                            headers=headers,
                            org=org
                        )
                    for repo in repos:
                        branches = self.get_branches(
                            url=h['api_url'],
                            headers=headers,
                            org=org,
                            repo=repo
                        )
                        pulls = get_pull_requests(
                            hoster=h['name'],
                            url=h['api_url'],
                            headers=headers,
                            org=org,
                            repo=repo,
                            state='open'
                        )
                        if branches:
                            result_branches = self.get_empty_branches(
                                hoster=h['name'],
                                org=org,
                                repo=repo,
                                pulls=pulls,
                                branches=branches)
                            empty_branches.extend(result_branches)

        return create_result(empty_branches)
