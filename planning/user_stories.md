# Attention List
This document contains all user stories for the tool `attention_list` and its
components.

## General Description

The overall target is to gather information out of Git repositories and its branches which
might be fixed or in another way manually processed. The tool can be invoked
via CLI or other processing engines like CI/CD systems. For the usage a
user must provide general information like the git provider and authentication
credentials.

## User Stories
The user stories contain all necessary action points to be fulfilled by the
tool.

### User Story: Failed Builds or Check Runs  
A user runs the tool to list all failed Pull Requests or Check Runs of the last commit.
A bonus would be the reason of the occured issue.

al pull request list failed

### User Story: Pull Request is open but no Build run happens
A user runs the tool to list Pull Requests which are already open but the CI/CD tool Zuul does not build a preview.
The well known reasons are:

1. The repo is not known to Zuul
2. There are configuration errors in Zuul config (blue bell in Zuul dashboard)
3. Zuul outage / not available (recheck / regate)
4. There is no branch protection

al pull request list open

### User Story: Check is Hanging / timed out  
A user runs the tool to list all failed Pull Requests where a check is hanging or runs into timeout.

Site note: 3 hours timeout for Zuul checkrun / job

al pull request list timeout

### User Story: PR doc-export is closed but specific PR remains open  
A user runs the tool to list all issues where a Pull Request in doc-export repository has been closed but the corresponding Pull Request in the specific service repository remains open.


al pull request list orphans
### User Story: Branches without open PR  
A user runs the tool to list all branches which do not have open Pull Request at all and might be deleted.

al branch list empty
### User Story: Old Pull Requests
A user runs the tool to list all Pull Requests older then a particular age.

al pull request list older <age>
### User Story: Zuul Errors
A user runs the tool to list all Zuul errors (blue bell).

al zuul list errors
### User Story: Not existing Repositories required by metadata
A user runs the tool to list all not existing repositories which are required by metadata (vgl. metadata/services.yaml with github / gitea).

al repository list not existing
### User Story: Not existing folders
A user runs the tool to list all not existing folders of metadata/services.yaml `html_location -> doc-exports`; `rst_location -> specific service repo`

al metadata list folders not existing
### User Story: Repositories not known to Zuul
A user runs the tool to list all Repositories is not known  to Zuul (main.yaml: https://github.com/opentelekomcloud-infra/zuul-config/blob/main/zuul/main.yaml) from `metadata/services.yaml`.

al zuul list repositories unknown