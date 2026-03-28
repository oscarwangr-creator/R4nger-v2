# port_scan

## Purpose
Port Scan capability for infrastructure intelligence workflows.

## Pipeline Coverage
- Stage labels: G
- YAML stage names: enrichment

## Input Schema
- input_types: ['ip', 'domain']
- consumes variables: []

## Output Schema
- output_types: ['open_port']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - port_scan
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
