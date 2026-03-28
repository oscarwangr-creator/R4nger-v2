# domain_whois

## Purpose
Domain Whois capability for domain intelligence workflows.

## Pipeline Coverage
- Stage labels: F
- YAML stage names: enrichment, collection

## Input Schema
- input_types: ['domain']
- consumes variables: []

## Output Schema
- output_types: ['whois_record']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - domain_whois
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
