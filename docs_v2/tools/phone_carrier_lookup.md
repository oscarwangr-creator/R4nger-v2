# phone_carrier_lookup

## Purpose
Phone Carrier Lookup capability for phone intelligence workflows.

## Pipeline Coverage
- Stage labels: L
- YAML stage names: collection

## Input Schema
- input_types: ['phone']
- consumes variables: []

## Output Schema
- output_types: ['carrier_record']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - phone_carrier_lookup
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
