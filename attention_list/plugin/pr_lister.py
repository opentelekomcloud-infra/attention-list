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


git_hoster = ['gitea', 'github']
github_api_url = 'https://api.github.com/'

class PrLister:
    def __init__(self, config, args):
        self.config = config.get_config()
        self.args = args
        self.created_at = None
        self.error = None
        self.host = None
        self.org = None
        self.pullrequest = None
        self.repo = None
        self.status = None
        self.updated_at = None
        self.url = None
        self.zuul_url = None
    
    def print_config(self):
        print(self.config)

    def check_config(self):
        if not self.config['pr_list_failed']['git_hoster']:
            raise Exception('Config missing git_hoster entry.')
        hoster = self.config['pr_list_failed']['git_hoster']
        for h in hoster:
            if h['name'] not in git_hoster:
                raise Exception('git_hoster[\'name\'] wrong: ' + h['name'])
            elif not h['api_url']:
                    raise Exception('git_hoster[\'api_url\'] missing '
                                    'for git_hoster: ' + h['name'])
            elif (not h['orgs']) or (not isinstance(h['orgs'], list)):
                    raise Exception('git_hoster[\'orgs\'] missing '
                                    'or not type of list for git_hoster: '
                                    + h['name'])
        

    def list_failed_pr(self):
        self.print_config()
        self.check_config()
        exit()
        self.hoster = self.config['pr_list_failed']['git_hoster']

        failed_commits = []
        for h in self.hoster:
            if h['name'] == 'gitea':
### stop point
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

