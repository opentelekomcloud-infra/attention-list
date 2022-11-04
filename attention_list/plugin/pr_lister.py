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

git_hoster = ['gitea', 'github']


class FailedPR:
    """Base class for failed Pull Requests"""
    def __init__(
            self,
            created_at,
            host,
            updated_at,
            url,
            error=None,
            pullrequest=None,
            org=None,
            repo=None,
            status=None,
            zuul_url=None):

        self.created_at = created_at
        self.error = error
        self.host = host
        self.org = org
        self.pullrequest = pullrequest
        self.repo = repo
        self.status = status
        self.updated_at = updated_at
        self.url = url
        self.zuul_url = zuul_url


class PrLister:
    """
    Base class which has all methods to create a list of failed Pull Requests
    from GitHub or Gitea repositories.
    """
    def __init__(self, config, args):
        self.config = config.get_config()
        self.args = args

    def print_config(self):
        print(self.config)

    def check_config(self):
        if not self.config['pr_list_failed']['git_hoster']:
            raise Exception('Config missing git_hoster entry.')
        hoster = self.config['pr_list_failed']['git_hoster']
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
                        repositories.append(repo)
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
            print("Get Gitea pullrequests error: " + str(e))
            print(
                "The request status is: "
                + str(res.status_code)
                + " | "
                + str(res.reason))
            exit()
        return pullrequests

    def add_builds_to_obj(self, obj, url, tenant):
        """
        This method trys to find all build jobs under a Zuul buildset.
        The corresponding data like log_url and status will be added.
        """
        zuul_api_url = "https://zuul.otc-service.com/api/tenant/"
        zuul_api_url = zuul_api_url + tenant + "/buildset/"
        final_url = re.sub(r'.*\/buildset\/', zuul_api_url, url)
        headers = {}
        headers['accept'] = 'application/json'
        res_zuul = requests.request('GET', url=final_url, headers=headers)
        if res_zuul.status_code != 404 and res_zuul.json():
            x = res_zuul.json()
            if ('builds' in x) and (len(x['builds']) != 0):
                jobs = []
                for build in x['builds']:
                    job = {}
                    job['uuid'] = build['uuid']
                    job['name'] = build['job_name']
                    job['result'] = build['result']
                    job['log_url'] = build['log_url']
                    jobs.append(job)
                obj.jobs = jobs
        return obj

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

    def get_gitea_failed_commits(self, pull, url, gitea_org, repo, headers):
        """
        Collect all failed gitea commits of one repository.
        """
        failed_commits = []
        try:
            req_url = (
                url
                + 'repos/'
                + gitea_org
                + '/'
                + repo['name']
                + '/commits/'
                + pull['head']['ref']
                + '/statuses?limit=1')
            res_sta = requests.request('GET', url=req_url, headers=headers)
            if res_sta.json():
                if res_sta.json()[0]['status'] == 'failure':
                    zuul_url = res_sta.json()[0]['target_url']
                    o = FailedPR(
                        host='gitea',
                        url=pull['url'],
                        org=gitea_org,
                        repo=repo['name'],
                        pullrequest=pull['title'],
                        status=res_sta.json()[0]['status'],
                        zuul_url=zuul_url,
                        created_at=pull['created_at'],
                        updated_at=res_sta.json()[0]['updated_at'],
                        error=1000
                    )
                    o = self.add_builds_to_obj(
                        obj=o,
                        url=zuul_url,
                        tenant='gl')
                    failed_commits.append(o)

        except Exception as e:
            print("Get Gitea failed commits error: " + str(e))
            print(
                "The request status is: "
                + str(res_sta.status_code)
                + " | "
                + str(res_sta.reason))
        return failed_commits

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

    def get_github_failed_commits(self, pull, url, github_org, repo, headers):
        """
        Collect all Failed Pull Requests of one GitHub repository
        """
        failed_commits = []
        try:
            req_url = (
                url
                + 'repos/'
                + github_org
                + '/'
                + repo['name']
                + '/commits/'
                + pull['head']['sha']
                + '/check-runs')
            res_sta = requests.request('GET', url=req_url, headers=headers)
        except Exception as e:
            print("Get GitHub failed commits error: " + str(e))
            print(
                "The request status is: "
                + str(res_sta.status_code)
                + " | "
                + str(res_sta.reason))

        if res_sta.json():
            if len(res_sta.json()['check_runs']) != 0:
                if res_sta.json()['check_runs'][0]['conclusion'] == 'failure':
                    zuul_url = res_sta.json()['check_runs'][0]['details_url']
                    o = FailedPR(
                        host='github',
                        url=pull['html_url'],
                        org=github_org,
                        repo=repo['name'],
                        pullrequest=pull['title'],
                        status=res_sta.json()['check_runs'][0]['conclusion'],
                        zuul_url=zuul_url,
                        created_at=pull['created_at'],
                        updated_at=(res_sta.json()['check_runs']
                                    [0]['completed_at']),
                        error=1000
                    )
                    o = self.add_builds_to_obj(
                        obj=o,
                        url=zuul_url,
                        tenant='eco')
                    failed_commits.append(o)
            else:
                o = FailedPR(
                    host='github',
                    url=pull['html_url'],
                    org=github_org,
                    repo=repo['name'],
                    pullrequest=pull['title'],
                    created_at=pull['created_at'],
                    updated_at=pull['updated_at'],
                    error=1001,
                )
                failed_commits.append(o)

        return failed_commits

    def create_result(self, failed_commits):
        """
        Create dictionary result list.
        """
        result = {}
        result['meta'] = {}
        result['data'] = []
        if len(failed_commits) != 0:
            failed_commits_json = []
            for obj in failed_commits:
                failed_commits_json.append(vars(obj))
            result['meta']['count'] = len(failed_commits_json)
            result['data'] = failed_commits_json
        else:
            result['meta']['count'] = 0

        return result

    def list_failed_pr(self):
        """
        Method to run through every repository in each organization of one
        or more Git providers.
        """
        self.check_config()
        self.hoster = self.config['pr_list_failed']['git_hoster']

        failed_commits = []
        for h in self.hoster:
            if h['name'] == 'gitea':
                headers = get_headers(
                    hoster=h['name'],
                    args=self.args
                )
                for org in h['orgs']:
                    repos = self.get_gitea_repos(
                        url=h['api_url'],
                        headers=headers,
                        gitea_org=org
                    )
                    for repo in repos:
                        pulls = self.get_gitea_prs(
                            url=h['api_url'],
                            headers=headers,
                            gitea_org=org,
                            repo=repo['name']
                        )
                        if pulls:
                            for pull in pulls:
                                commits = self.get_gitea_failed_commits(
                                    pull=pull,
                                    url=h['api_url'],
                                    gitea_org=org,
                                    repo=repo,
                                    headers=headers
                                )
                                failed_commits.extend(commits)

            elif h['name'] == 'github':
                headers = get_headers(
                    hoster=h['name'],
                    args=self.args
                )
                for org in h['orgs']:
                    repos = self.get_github_repos(
                        url=h['api_url'],
                        headers=headers,
                        github_org=org
                    )
                    for repo in repos:
                        pulls = self.get_github_prs(
                            url=h['api_url'],
                            headers=headers,
                            github_org=org,
                            repo=repo['name']
                        )
                        if pulls:
                            for pull in pulls:
                                commits = self.get_github_failed_commits(
                                    pull=pull,
                                    url=h['api_url'],
                                    github_org=org,
                                    repo=repo,
                                    headers=headers
                                )
                                failed_commits.extend(commits)

        return self.create_result(failed_commits)
