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


class AttentionList:
    def __init__(self):
        self.config = None
    
    def create_parser(self):
        parser = argparse.ArgumentParser(description="AttentionList Controller")
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
        print('PR Lister')
        if self.args.failed:
            print(self.args.failed)
    
    def metadata_lister(self):
        print('Metadata Lister')
    
    def zuul_lister(self):
        print('Zuul Lister')

    def parse_arguments(self, args=None):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args(args)
    
    def main(self, args=None):
        self.parse_arguments(args)
        try:
            self.args.func()
        except Exception as e:
            print(e)

def main():
    AttentionList().main()

if __name__ == '__main__':
    main()
