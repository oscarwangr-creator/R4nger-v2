# leak_corpus_search

## Purpose
Leak Corpus Search capability for breach intelligence workflows.

## Pipeline Coverage
- Stage labels: I
- YAML stage names: enrichment

## Input Schema
- input_types: ['email', 'username']
- consumes variables: []

## Output Schema
- output_types: ['leak_record']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - leak_corpus_search
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
