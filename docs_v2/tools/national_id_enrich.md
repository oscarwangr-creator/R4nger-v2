# national_id_enrich

## Purpose
National Id Enrich capability for identity intelligence workflows.

## Pipeline Coverage
- Stage labels: A, K
- YAML stage names: enrichment

## Input Schema
- input_types: ['identity']
- consumes variables: []

## Output Schema
- output_types: ['identity_record']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - national_id_enrich
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
