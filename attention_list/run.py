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


class AttentionListZuul():
    @classmethod
    def argparse_arguments(cls, parser):
        subparsers = parser.add_subparsers()
        subparsers_chooser = subparsers.add_parser('miau')
        subparsers_chooser = subparsers.add_parser('muh')


class AlPRLister():
    @classmethod
    def argparse_arguments(cls, parser):
        parser.add_argument('option')


class AttentionListPR():
    @classmethod
    def argparse_arguments(cls, parser):
        subparsers = parser.add_subparsers()
        subcontroller = subparsers.add_parser('list')
        AlPRLister.argparse_arguments(subcontroller)
        
        subcontroller = subparsers.add_parser('del')


class AttentionList:
    def __init__(self):
        self.config = None
    
    def create_parser(self):
        parser = argparse.ArgumentParser(description="AttentionList Controller")
        subparsers = parser.add_subparsers()

        controller_parser = subparsers.add_parser('pr', help="pr parser")
        AttentionListPR.argparse_arguments(controller_parser)


        controller_parser = subparsers.add_parser('zuul', help="zuul parser")
        AttentionListZuul.argparse_arguments(controller_parser)

        
        return parser

    def parse_arguments(self, args=None):
        parser = self.create_parser()
        self.args = parser.parse_args(args)

        return parser
    
    def main(self):
        self.parse_arguments()

def main():
    AttentionList().main()

if __name__ == '__main__':
    main()
