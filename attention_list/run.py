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

import argparse
import logging
import json
import yaml
from yaml.loader import SafeLoader

# after building package: plugin -> attention_list.plugin
from plugin import pr_lister


class AlConfig():
    def __init__(self):
        self.config = None
    
    def get_config(self):
        return self.config


class AttentionList:
    def __init__(self):
        self.config = None
    
    def create_parser(self):
        parser = argparse.ArgumentParser(
            description='AttentionList - A tool collecting '
                        'issues about Helpcenter 2.0')
        parser.add_argument(
            '--config',
            default='config.yaml',
            help='Path and name to yaml configuration file')
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Set debug mode on.'
        )
        parser.add_argument(
            '--yaml',
            action='store_true',
            help='Set yaml output format instead of json.'
        )
        self.createCommandParsers(parser)
        
        return parser

    def createCommandParsers(self, parser):
        subparsers = parser.add_subparsers(title='commands')

        self.add_branch_subparser(subparsers)
        self.add_metadata_subparser(subparsers)
        self.add_pr_subparser(subparsers)
        self.add_zuul_subparser(subparsers)
  
        return subparsers
    
    def add_branch_subparser(self, subparsers):
        cmd_branch = subparsers.add_parser('branch', help='Branch parser')
        cmd_branch_subparsers = cmd_branch.add_subparsers()

        self.add_branch_list_subparser(cmd_branch_subparsers)
    
    def add_branch_list_subparser(self, subparsers):
        cmd_branch_list = subparsers.add_parser('list', help='Branch lister parser')
        cmd_branch_list.add_argument(
            '--empty',
            action='store_true',
            help='List empty branches')
    
    def add_metadata_subparser(self, subparsers):
        cmd_metadata = subparsers.add_parser('metadata', help='Metadata parser')
        cmd_metadata_subparsers = cmd_metadata.add_subparsers()

        self.add_metadata_list_subparser(cmd_metadata_subparsers)
    
    def add_metadata_list_subparser(self, subparsers):
        cmd_metadata_list = subparsers.add_parser('list', help='Metadata lister parser')
        cmd_metadata_list.add_argument(
            '--not-existing-folders',
            action='store_true',
            help='List not existing folders in metadata/services.yaml')

        cmd_metadata_list.set_defaults(func=self.metadata_lister)

    def add_pr_subparser(self, subparsers):
        cmd_pr = subparsers.add_parser('pr', help='PR parser')
        cmd_pr_subparsers = cmd_pr.add_subparsers()

        self.add_pr_list_subparser(cmd_pr_subparsers)
    
    def add_pr_list_subparser(self, subparsers):
        cmd_pr_list = subparsers.add_parser('list', help='PR lister parser')
        cmd_pr_list.add_argument(
            '--failed',
            action='store_true',
            help='List failed PRs')
        cmd_pr_list.add_argument(
            '--open',
            action='store_true',
            help='List open PRs')
        cmd_pr_list.add_argument(
            '--timeout',
            action='store_true',
            help='List timeout PRs')
        cmd_pr_list.add_argument(
            '--orphans',
            action='store_true',
            help='List orphan PRs')
        cmd_pr_list.add_argument(
            '--older',
            type=int,
            metavar='DAYS',
            help='List PRs older than <value in days>')
        cmd_pr_list.add_argument(
            '--github-token',
            help='Provide GitHub token via CLI')
        cmd_pr_list.add_argument(
            '--gitea-token',
            help='Provide Gitea token via CLI')

        cmd_pr_list.set_defaults(func=self.pr_lister)

    def add_zuul_subparser(self, subparsers):
        cmd_zuul = subparsers.add_parser('zuul', help='Zuul parser')
        cmd_zuul_subparsers = cmd_zuul.add_subparsers()

        self.add_zuul_list_subparser(cmd_zuul_subparsers)
    
    def add_zuul_list_subparser(self, subparsers):
        cmd_zuul_list = subparsers.add_parser('list', help='Zuul lister parser')
        cmd_zuul_list.add_argument(
            '--error',
            action='store_true',
            help='List Zuul errors.')
        cmd_zuul_list.add_argument(
            '--unknown-repos',
            action='store_true',
            help='List unknown repositories for Zuul.')

        cmd_zuul_list.set_defaults(func=self.zuul_lister)

    def branch_lister(self):
        print('Branch Lister')

    def pr_lister(self):
        if not (
            self.args.failed or
            self.args.open or
            self.args.timeout or
            self.args.orphans or
            self.args.older):
            raise Exception('PullRequest list parameter missing.')
        lister = pr_lister.PrLister(config=self.config, args=self.args)
        self.create_result(lister.list_failed_pr())
    
    def metadata_lister(self):
        print('Metadata Lister')
    
    def zuul_lister(self):
        print('Zuul Lister')

    def parse_arguments(self, args=None):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args(args)
    
    def read_config_file(self):
        try:
            with open(self.args.config) as f:
                config = yaml.load(f, Loader=SafeLoader)
        except Exception as e:
            print('ERROR while loading config file: ' + self.args.config)
        return config
    
    def create_result(self, data):
        if data:
            if self.args.yaml:
                result = yaml.dump(data)
            else:
                result= json.dumps(data)
        else:
            raise("Result data missing")
        
        print(result)

    def main(self, args=None):
        self.parse_arguments(args)

        if self.args.debug:
            logging.basicConfig(level=logging.DEBUG)

        self.config = AlConfig()
        self.config.config = self.read_config_file()

        # Rework
        # try:
        self.args.func()
        # except Exception:
            # self.parser.print_help()

            


def main():
    AttentionList().main()

if __name__ == '__main__':
    main()
