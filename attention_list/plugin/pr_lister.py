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


import json
import yaml
import requests
import json
import re
import os
import yaml

git_hoster = ['gitea', 'github']
github_api_url = 'https://api.github.com/'


class PrLister:
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
    
    def get_headers(self, hoster, args):
        headers = {}
        headers['accept'] = 'application/json'
        headers['Authorization'] = 'token ' + get_token(
            hoster=hoster,
            args=args
        )

        return headers
    
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
        
    def list_failed_pr(self):
        self.print_config()
        self.check_config()
        self.hoster = self.config['pr_list_failed']['git_hoster']

        failed_commits = []
        for h in self.hoster:
            if h['name'] == 'gitea':
                headers = self.get_headers(
                    hoster=h['name'],
                    args=self.args
                )
                for org in h['orgs']:
                    repos = get_gitea_repos(
                        url=h['api_url'],
                        headers=headers,
                        gitea_org=org
                    )
                    for repo in repos:
                        print(repo)
                        # pulls = get_gitea_prs(
                        #     url=h['api_url'],
                        #     headers=headers,
                        #     gitea_org=org,
                        #     repo=repo['name']
                        # )
                        # if pulls:
                        #     for pull in pulls:
                        #         commits = get_gitea_failed_commits(
                        #             pull=pull,
                        #             url=h['api_url'],
                        #             gitea_org=org,
                        #             repo=repo,
                        #             headers=headers
                        #         )
                        #         failed_commits.extend(commits)

            # elif h == 'github':
            #     if not args.github_url:
            #         raise ValueError('Parameter --github-url not found.')
            #     url = args.github_url
            #     headers = {}
            #     headers['accept'] = 'application/json'
            #     headers['Authorization'] = 'Bearer ' + get_token(
            #         hoster=h,
            #         args=args
            #     )

            #     for org in args.github_orgs:
            #         repos = get_github_repos(
            #             url=url,
            #             headers=headers,
            #             github_org=org
            #         )
            #         for repo in repos:
            #             pulls = get_github_prs(
            #                 url=url,
            #                 headers=headers,
            #                 github_org=org,
            #                 repo=repo['name']
            #             )
            #             if pulls:
            #                 for pull in pulls:
            #                     commits = get_github_failed_commits(
            #                         pull=pull,
            #                         url=url,
            #                         github_org=org,
            #                         repo=repo,
            #                         headers=headers
            #                     )
            #                     failed_commits.extend(commits)
        
        exit()
        result = create_result(failed_commits=failed_commits)
        if args.yaml:
            result = yaml.dump(result)
        else:
            result = json.dumps(result)

