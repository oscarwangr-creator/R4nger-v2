# full_contact_lookup

## Purpose
Full Contact Lookup capability for identity intelligence workflows.

## Pipeline Coverage
- Stage labels: A, K
- YAML stage names: enrichment, collection

## Input Schema
- input_types: ['identity']
- consumes variables: []

## Output Schema
- output_types: ['entity_profile']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - full_contact_lookup
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
