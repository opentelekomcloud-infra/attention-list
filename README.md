# attention-list
Tool to list issues related to our documentation platform

## Dev installation

```
git clone git@github.com:opentelekomcloud-infra/attention-list.git
cd attention-list
python setup.py develop
```

## Available commands

```
attentionlist pr list --failed
attentionlist pr list --orphans
attentionlist zuul list --errors
attentionlist branch list --empty
```

## Configuration File

For proper configuration a config file can be found in templates folder: https://github.com/opentelekomcloud-infra/attention-list/blob/main/templates/config.yaml
