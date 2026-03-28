# exposed_service_discovery

## Purpose
Exposed Service Discovery capability for attack_surface intelligence workflows.

## Pipeline Coverage
- Stage labels: G
- YAML stage names: collection, enrichment

## Input Schema
- input_types: ['domain', 'ip']
- consumes variables: []

## Output Schema
- output_types: ['service_exposure']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - exposed_service_discovery
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
