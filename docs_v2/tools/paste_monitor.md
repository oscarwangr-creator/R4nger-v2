# paste_monitor

## Purpose
Paste Monitor capability for breach intelligence workflows.

## Pipeline Coverage
- Stage labels: I
- YAML stage names: collection

## Input Schema
- input_types: ['email', 'username']
- consumes variables: []

## Output Schema
- output_types: ['paste_hit']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - paste_monitor
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
