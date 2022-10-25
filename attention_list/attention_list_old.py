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

# Error Codes
# 1000: Failed check (default error)
# 1001: Check not existing but expected

import argparse
import logging
import requests
import json
import re
import os
import yaml


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


def get_args():
    """
    Function to collect parameter.
    """
    parser = argparse.ArgumentParser(
        description='Bootstrap repositories.')
    parser.add_argument(
        '--github-orgs',
        nargs='+',
        default=['opentelekomcloud-docs'],
        help='One or more GitHub organizations to be queried for failed Pull '
             'Requests.\n'
             'Default: [opentelekomcloud-docs]'
    )
    parser.add_argument(
        '--gitea-orgs',
        nargs='+',
        default=['docs'],
        help='One or more Gitea organizations to be queried for failed Pull '
             'Requests.\n'
             'Default: [docs]'
    )
    parser.add_argument(
        '--github-token',
        help='API Token for GitHub.'
    )
    parser.add_argument(
        '--gitea-token',
        help='API Token for Gitea'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Set debug mode on.'
    )
    parser.add_argument(
        '--gitea-url',
        default='https://gitea.eco.tsi-dev.otc-service.com/api/v1/',
        help='Gitea base URL for API request.\n'
             'Default: https://gitea.eco.tsi-dev.otc-service.com/api/v1/'
    )
    parser.add_argument(
        '--github-url',
        default='https://api.github.com/',
        help='GitHub Base URL for API request.\n'
             'Default: https://api.github.com/'
    )
    parser.add_argument(
        '--hoster',
        default=['gitea', 'github'],
        nargs='+',
        help='Git hoster to be queried for failed Pull Requests.\n'
             'Default: [github, gitea].'
    )
    parser.add_argument(
        '--yaml',
        action='store_true',
        help='Set yaml output format instead of json.'
    )
    return parser.parse_args()


def add_builds_to_obj(obj, url, tenant):
    """
    This method trys to find all build jobs under a Zuul buildset.
    The corresponding data like log_url and status will be added.
    """
    zuul_api_url = "https://zuul.otc-service.com/api/tenant/" + tenant + "/buildset/"
    final_url = re.sub('.*\/buildset\/', zuul_api_url, url)
    zuul_headers = {}
    zuul_headers['accept'] = 'application/json'
    res_zuul = requests.request('GET', url=final_url, headers=zuul_headers)
    if res_zuul.status_code != 404 and res_zuul.json():
        x = res_zuul.json()
        if len(x['builds']) != 0:
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


def get_gitea_repos(url, headers, gitea_org):
    """
    Get all Repositories of one Gitea orgainzation
    """
    repositories = []
    i = 1

    while True:
        try:
            req_url = (url
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
            print("An error has occured: " + str(e))
            print("The request status is: " + str(res.status_code) +
                  " | " + str(res.reason))
            break
    return repositories





def get_github_repos(url, headers, github_org):
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
            print("An error has occured: " + str(e))
            print("The request status is: " + str(res.status_code) +
                  " | " + str(res.reason))
            break
    return repositories


def get_github_prs(url, headers, github_org, repo):
    """
    Get all Pull Requests of one GitHub repository
    """
    pullrequests = []
    i = 1

    while True:
        try:
            req_url = (url + 'repos/' + github_org + '/' + repo +
                       '/pulls?state=open&page=' + str(i))
            res = requests.request('GET', url=req_url, headers=headers)
            if res.json():
                for pr in res.json():
                    pullrequests.append(pr)
                i += 1
                continue
            else:
                break
        except Exception as e:
            print("An error has occured: " + str(e))
            print("The request status is: " + str(res.status_code) +
                  " | " + str(res.reason))
            break
    return pullrequests


def get_github_failed_commits(pull, url, github_org, repo, headers):
    """
    Collect all Failed Pull Requests of one GitHub repository
    """
    failed_commits = []
    try:
        req_url = (url + 'repos/' + github_org + '/' + repo['name'] +
                   '/commits/' + pull['head']['sha'] + '/check-runs')
        res_sta = requests.request('GET', url=req_url, headers=headers)
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
                    o = add_builds_to_obj(obj=o, url=zuul_url, tenant='eco')
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

    except Exception as e:
        print("An error has occured: " + str(e))
        print("The request status is: " + str(res_sta.status_code) +
              " | " + str(res_sta.reason))
    return failed_commits


def create_result(failed_commits):
    """
    Create Result
    """
    result = {}
    result['meta'] = {}
    result['data'] = []
    if len(failed_commits) != 0:
        failed_commits_json = []
        for o in failed_commits:
            failed_commits_json.append(vars(o))
        result['meta']['count'] = len(failed_commits_json)
        result['data'] = failed_commits_json
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
                'Please, provide GitHub Token as console argument or \n'
                'as environment variable GITEA_TOKEN')
    else:
        raise ValueError('No supported Git hoster provided.')
    return token


def main():
    args = get_args()
    failed_commits = []

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    for h in args.hoster:
        if h == 'gitea':

            headers = {}
            headers['accept'] = 'application/json'
            headers['Authorization'] = 'token ' + get_token(
                hoster=h,
                args=args
            )

            if not args.gitea_url:
                raise Exception('Please, provide Gitea URL as argument.')

            for org in args.gitea_orgs:
                repos = get_gitea_repos(
                    url=args.gitea_url,
                    headers=headers,
                    gitea_org=org
                )
                for repo in repos:
                    pulls = get_gitea_prs(
                        url=args.gitea_url,
                        headers=headers,
                        gitea_org=org,
                        repo=repo['name']
                    )
                    if pulls:
                        for pull in pulls:
                            commits = get_gitea_failed_commits(
                                pull=pull,
                                url=args.gitea_url,
                                gitea_org=org,
                                repo=repo,
                                headers=headers
                            )
                            failed_commits.extend(commits)

        elif h == 'github':
            if not args.github_url:
                raise ValueError('Parameter --github-url not found.')
            url = args.github_url
            headers = {}
            headers['accept'] = 'application/json'
            headers['Authorization'] = 'Bearer ' + get_token(
                hoster=h,
                args=args
            )

            for org in args.github_orgs:
                repos = get_github_repos(
                    url=url,
                    headers=headers,
                    github_org=org
                )
                for repo in repos:
                    pulls = get_github_prs(
                        url=url,
                        headers=headers,
                        github_org=org,
                        repo=repo['name']
                    )
                    if pulls:
                        for pull in pulls:
                            commits = get_github_failed_commits(
                                pull=pull,
                                url=url,
                                github_org=org,
                                repo=repo,
                                headers=headers
                            )
                            failed_commits.extend(commits)
        else:
            raise ValueError("No supported hoster found.")

    result = create_result(failed_commits=failed_commits)
    if args.yaml:
        result = yaml.dump(result)
    else:
        result = json.dumps(result)

    print(result)


if __name__ == '__main__':
    main()
