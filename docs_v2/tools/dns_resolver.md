# dns_resolver

## Purpose
Dns Resolver capability for domain intelligence workflows.

## Pipeline Coverage
- Stage labels: F
- YAML stage names: enrichment

## Input Schema
- input_types: ['domain']
- consumes variables: []

## Output Schema
- output_types: ['dns_record']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - dns_resolver
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
