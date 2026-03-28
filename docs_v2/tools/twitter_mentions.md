# twitter_mentions

## Purpose
Twitter Mentions capability for socmint intelligence workflows.

## Pipeline Coverage
- Stage labels: C
- YAML stage names: enrichment, collection

## Input Schema
- input_types: ['username']
- consumes variables: []

## Output Schema
- output_types: ['mention']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - twitter_mentions
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
