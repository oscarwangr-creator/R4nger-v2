# phone_reputation_check

## Purpose
Phone Reputation Check capability for phone intelligence workflows.

## Pipeline Coverage
- Stage labels: L
- YAML stage names: enrichment

## Input Schema
- input_types: ['phone']
- consumes variables: []

## Output Schema
- output_types: ['reputation']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - phone_reputation_check
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
