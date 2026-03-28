# ip_geolocation

## Purpose
Ip Geolocation capability for geoint intelligence workflows.

## Pipeline Coverage
- Stage labels: J
- YAML stage names: enrichment, collection

## Input Schema
- input_types: ['ip']
- consumes variables: []

## Output Schema
- output_types: ['location']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - ip_geolocation
    input:
      value: {{value}}
```

## Dependencies
['satellite_context']

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
