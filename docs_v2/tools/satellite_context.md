# satellite_context

## Purpose
Satellite Context capability for geoint intelligence workflows.

## Pipeline Coverage
- Stage labels: J
- YAML stage names: enrichment

## Input Schema
- input_types: ['location']
- consumes variables: []

## Output Schema
- output_types: ['imagery_context']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - satellite_context
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
