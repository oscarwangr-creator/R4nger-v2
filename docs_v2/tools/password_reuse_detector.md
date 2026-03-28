# password_reuse_detector

## Purpose
Password Reuse Detector capability for credential intelligence workflows.

## Pipeline Coverage
- Stage labels: H
- YAML stage names: enrichment

## Input Schema
- input_types: ['credential']
- consumes variables: []

## Output Schema
- output_types: ['reuse_signal']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - password_reuse_detector
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
