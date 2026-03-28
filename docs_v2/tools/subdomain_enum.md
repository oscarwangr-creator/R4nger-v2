# subdomain_enum

## Purpose
Subdomain Enum capability for infrastructure intelligence workflows.

## Pipeline Coverage
- Stage labels: G
- YAML stage names: collection, enrichment

## Input Schema
- input_types: ['domain']
- consumes variables: []

## Output Schema
- output_types: ['subdomain']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - subdomain_enum
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
