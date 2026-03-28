# cve_lookup

## Purpose
Cve Lookup capability for threatintel intelligence workflows.

## Pipeline Coverage
- Stage labels: D
- YAML stage names: enrichment, collection

## Input Schema
- input_types: ['cve', 'product']
- consumes variables: []

## Output Schema
- output_types: ['vulnerability']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - cve_lookup
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
