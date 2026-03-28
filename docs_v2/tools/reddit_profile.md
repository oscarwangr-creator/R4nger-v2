# reddit_profile

## Purpose
Reddit Profile capability for socmint intelligence workflows.

## Pipeline Coverage
- Stage labels: C
- YAML stage names: enrichment

## Input Schema
- input_types: ['username']
- consumes variables: []

## Output Schema
- output_types: ['reddit_profile']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - reddit_profile
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
