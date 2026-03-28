# email_validate

## Purpose
Email Validate capability for email intelligence workflows.

## Pipeline Coverage
- Stage labels: E
- YAML stage names: collection

## Input Schema
- input_types: ['email']
- consumes variables: []

## Output Schema
- output_types: ['email_validation']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - email_validate
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
