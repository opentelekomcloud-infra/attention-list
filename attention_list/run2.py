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

        self.add_pr_subparser(subparsers)
  
        return subparsers
    
    def add_pr_subparser(self, subparsers):
        cmd_pr = subparsers.add_parser('pr', help='pr parser')
        cmd_pr.add_argument('--count',
                            help='number of job runs (default: 1)',
                            default=1)
        cmd_pr.set_defaults(func=self.pr())
        self.cmd_pr = cmd_pr
    
    def pr(self):
        print('PR function')

    def parse_arguments(self, args=None):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args(args)
    
    def main(self, args=None):
        self.parse_arguments(args)
        self.args.func()
        print(self.cmd_pr)

def main():
    AttentionList().main()

if __name__ == '__main__':
    main()
