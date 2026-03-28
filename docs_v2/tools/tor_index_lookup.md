# tor_index_lookup

## Purpose
Tor Index Lookup capability for darkweb intelligence workflows.

## Pipeline Coverage
- Stage labels: D
- YAML stage names: collection, enrichment

## Input Schema
- input_types: ['email', 'domain']
- consumes variables: []

## Output Schema
- output_types: ['darkweb_hit']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - tor_index_lookup
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
