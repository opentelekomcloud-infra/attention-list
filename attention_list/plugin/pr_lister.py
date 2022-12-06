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
import datetime as dt
import dateutil.parser

from attention_list.helper.utils import check_config
from attention_list.helper.utils import create_result
from attention_list.helper.utils import get_headers
from attention_list.helper.utils import get_pull_requests
from attention_list.helper.utils import get_repos

git_hoster = ['gitea', 'github']


class PR:
    def __init__(
            self,
            created_at,
            updated_at,
            hoster,
            org,
            repo,
            title,
            url,
            state=None):

        self.created_at = created_at
        self.hoster = hoster
        self.org = org
        self.repo = repo
        self.title = title
        self.updated_at = updated_at
        self.url = url
        self.state = state


class OrphanPR:
    def __init__(
            self,
            title,
            url,
            state=None):

        self.title = title
        self.url = url
        self.state = state


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

    def get_failed_commits(self, hoster, pull, url, org, repo, headers):
        """
        Collect all Failed Pull Requests of a Git repository
        """
        failed_commits = []
        if hoster == 'gitea':
            req_url = (
                url
                + 'repos/'
                + org
                + '/'
                + repo
                + '/commits/'
                + pull['head']['ref']
                + '/statuses?limit=1')
            try:
                res = requests.request('GET', url=req_url, headers=headers)
            except Exception as e:
                print("Get Gitea failed commits error: " + str(e))
                print(
                    "The request status is: "
                    + str(res.status_code)
                    + " | "
                    + str(res.reason))
            if res.json():
                if res.json()[0]['status'] == 'failure':
                    zuul_url = res.json()[0]['target_url']
                    o = FailedPR(
                        host='gitea',
                        url=pull['url'],
                        org=org,
                        repo=repo,
                        pullrequest=pull['title'],
                        status=res.json()[0]['status'],
                        zuul_url=zuul_url,
                        created_at=pull['created_at'],
                        updated_at=res.json()[0]['updated_at'],
                        error=1000
                    )
                    o = self.add_builds_to_obj(
                        obj=o,
                        url=zuul_url,
                        tenant='gl')
                    failed_commits.append(o)

        elif hoster == 'github':
            req_url = (
                url
                + 'repos/'
                + org
                + '/'
                + repo
                + '/commits/'
                + pull['head']['sha']
                + '/check-runs')
            try:
                res = requests.request('GET', url=req_url, headers=headers)
            except Exception as e:
                print("Get GitHub failed commits error: " + str(e))
            if res.json():
                if len(res.json()['check_runs']) != 0:
                    if res.json()['check_runs'][0]['conclusion'] == 'failure':
                        zuul_url = res.json()['check_runs'][0]['details_url']
                        o = FailedPR(
                            host='github',
                            url=pull['html_url'],
                            org=org,
                            repo=repo,
                            pullrequest=pull['title'],
                            status=res.json()['check_runs'][0]['conclusion'],
                            zuul_url=zuul_url,
                            created_at=pull['created_at'],
                            updated_at=(res.json()['check_runs']
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
                        org=org,
                        repo=repo,
                        pullrequest=pull['title'],
                        created_at=pull['created_at'],
                        updated_at=pull['updated_at'],
                        error=1001,
                    )
                    failed_commits.append(o)
        return failed_commits

    def get_old_pulls(self, hoster, now, org, pulls, repo, days):
        """
        Get Pull Requests of a specific Git Repo which are older than
        specified value of days.

        :param hoster: Name of Git hoster
        :type hoster: string
        :param now: datetime object of the current time in UTC
        :type now: _type_
        :param org: Name of the current organization
        :type org: string
        :param repo: Name of the current repo
        :type repo:
        :param pulls: List of Pull Requests in dict format
        :type pulls: list
        :param args: string objects which represents the time difference
        of 'now'
        :returns: List of Pull Requests older than the time arguments
        :rtype: list
        """
        old_pulls = []
        seconds = days * 86400

        for pull in pulls:
            pull_time = dateutil.parser.isoparse(pull['created_at'])
            time_diff = (now - pull_time).total_seconds()
            if time_diff > seconds:
                if hoster == 'gitea':
                    obj = PR(
                        created_at=pull['created_at'],
                        hoster=hoster,
                        org=org,
                        repo=repo,
                        title=pull['title'],
                        updated_at=pull['updated_at'],
                        url=pull['html_url'],
                        state=pull['state']
                    )
                    old_pulls.append(obj)
                if hoster == 'github':
                    obj = PR(
                        created_at=pull['created_at'],
                        hoster=hoster,
                        org=org,
                        repo=repo,
                        title=pull['title'],
                        updated_at=pull['updated_at'],
                        url=pull['html_url'],
                        state=pull['state']
                    )
                    old_pulls.append(obj)

        return old_pulls

    def list(self):
        if self.args.failed:
            return self.list_failed_pr()
        elif self.args.orphans:
            return self.list_orphans()
        elif self.args.timeout:
            pass
        elif self.args.older:
            return self.list_older_pr()
        else:
            raise Exception('PrLister.list() failed due to missing arguments')

    def list_failed_pr(self):
        """
        command: pr list failed

        Method to run through every repository in each organization of one
        or more Git providers to get failed PR.
        """
        check_config(command='pr_list_failed', config=self.config)
        self.hoster = self.config['pr_list_failed']['git_hoster']

        failed_commits = []
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
                        pulls = get_pull_requests(
                            hoster=h['name'],
                            url=h['api_url'],
                            headers=headers,
                            org=org,
                            repo=repo,
                            state='open'
                        )
                        if pulls:
                            for pull in pulls:
                                commits = self.get_failed_commits(
                                    hoster=h['name'],
                                    pull=pull,
                                    url=h['api_url'],
                                    org=org,
                                    repo=repo,
                                    headers=headers
                                )
                                failed_commits.extend(commits)

        return create_result(failed_commits)

    def list_orphans(self):
        """
        command: pr list --orphans

        This method uses a defined repository as reference.
        The subsidiary PRs in other repositories are
        searched and the states are checked.
        An orphan PR is listed if the reference PR is closed and the
        linked PR remains open. If all linked PRs are closed and the
        reference PR is still open, than the reference PR is an orphan and will
        be listed.
        """
        check_config(command='pr_list_orphans', config=self.config)
        self.hoster = self.config['pr_list_orphans']['git_hoster']

        matrix = {}
        orphans = []
        for h in self.hoster:
            if h['name'] == 'gitea' or h['name'] == 'github':
                headers = get_headers(
                    hoster=h['name'],
                    args=self.args
                )
                for org in h['orgs']:
                    ref_pulls = get_pull_requests(
                        hoster=h['name'],
                        url=h['api_url'],
                        headers=headers,
                        org=org,
                        repo=h['ref_repo'],
                        state='open'
                    )
                    for pull in ref_pulls:
                        matrix[str(pull['number'])] = {
                            'title': pull['title'],
                            'url': pull['url'],
                            'state': pull['state'],
                            'pulls': []
                        }
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
                        if repo == h['ref_repo']:
                            continue
                        pulls = get_pull_requests(
                            hoster=h['name'],
                            url=h['api_url'],
                            headers=headers,
                            org=org,
                            repo=repo,
                        )
                        if pulls:
                            for pull in pulls:
                                ref_num = re.findall(
                                    r"docs\/doc-exports#([\d]+)",
                                    pull['title'])
                                if ref_num:
                                    if ref_num[0] in matrix:
                                        pull_format = {
                                            'title': pull['title'],
                                            'url': pull['url'],
                                            'state': pull['state']
                                        }
                                        matrix[ref_num[0]]['pulls'].append(
                                            pull_format
                                        )
                                    else:
                                        if pull['state'] == 'open':
                                            o = OrphanPR(
                                                title=pull['title'],
                                                url=pull['url'],
                                                state=pull['state']
                                            )
                                            orphans.append(o)
                for item in matrix:
                    if not matrix[item]['pulls']:
                        o = OrphanPR(
                            title=matrix[item]['title'],
                            url=matrix[item]['url'],
                            state=matrix[item]['state']
                        )
                        orphans.append(o)
                    else:
                        state_open = False
                        for p in matrix[item]['pulls']:
                            if p['state'] == 'open':
                                state_open = True

                        if not state_open:
                            o = OrphanPR(
                                title=matrix[item]['title'],
                                url=matrix[item]['url'],
                                state=matrix[item]['state']
                            )
                            orphans.append(o)

        return create_result(orphans)

    def list_older_pr(self):
        """
        command: pr list --older <age>

        Method to run through every repository in each organization of one
        or more Git providers.
        """
        check_config(command='pr_list_older', config=self.config)
        self.hoster = self.config['pr_list_older']['git_hoster']

        now = dt.datetime.now(dt.timezone.utc)

        old_pulls = []
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
                        pulls = get_pull_requests(
                            hoster=h['name'],
                            url=h['api_url'],
                            headers=headers,
                            org=org,
                            repo=repo,
                            state='open'
                        )
                        if pulls:
                            old_prs = self.get_old_pulls(
                                days=self.args.older,
                                hoster=h['name'],
                                pulls=pulls,
                                now=now,
                                org=org,
                                repo=repo,
                            )
                            old_pulls.extend(old_prs)

        return create_result(old_pulls)
