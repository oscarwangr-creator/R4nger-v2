# pdf_text_extract

## Purpose
Pdf Text Extract capability for document intelligence workflows.

## Pipeline Coverage
- Stage labels: C
- YAML stage names: collection

## Input Schema
- input_types: ['document']
- consumes variables: []

## Output Schema
- output_types: ['text']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - pdf_text_extract
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
