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


class AttentionList:
    def __init__(self):
        self.config = None
    
    def create_parser(self):
        parser = argparse.ArgumentParser(description="AttentionList Controller")
        parser.add_argument(
            "--config",
            dest="config",
            default="config.yaml",
            help="specify the config file",
        )
        subparsers = parser.add_subparsers(help="command help")
        
        AttentionListPR.argparse_arguments(subparsers)

        return parser

def main():
    AttentionList().main()

if __name__ == '__main__':
    main()
