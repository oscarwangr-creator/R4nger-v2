# email_breach_check

## Purpose
Email Breach Check capability for email intelligence workflows.

## Pipeline Coverage
- Stage labels: E
- YAML stage names: collection, enrichment

## Input Schema
- input_types: ['email']
- consumes variables: []

## Output Schema
- output_types: ['breach_hit']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - email_breach_check
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
