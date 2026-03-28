# document_metadata_extract

## Purpose
Document Metadata Extract capability for metadata intelligence workflows.

## Pipeline Coverage
- Stage labels: C
- YAML stage names: collection, enrichment

## Input Schema
- input_types: ['document']
- consumes variables: []

## Output Schema
- output_types: ['metadata']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - document_metadata_extract
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
