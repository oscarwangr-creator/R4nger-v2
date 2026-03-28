# github_username_intel

## Purpose
Github Username Intel capability for username intelligence workflows.

## Pipeline Coverage
- Stage labels: B
- YAML stage names: collection, enrichment

## Input Schema
- input_types: ['username']
- consumes variables: []

## Output Schema
- output_types: ['repo_activity']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - github_username_intel
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
