# image_exif_extract

## Purpose
Image Exif Extract capability for image intelligence workflows.

## Pipeline Coverage
- Stage labels: C
- YAML stage names: enrichment

## Input Schema
- input_types: ['image']
- consumes variables: []

## Output Schema
- output_types: ['exif']
- normalized keys: {'entities': 'list', 'relationships': 'list'}
- formats: JSON

## YAML Usage
```yaml
stages:
  - name: discovery
    tools:
      - image_exif_extract
    input:
      value: {{value}}
```

## Dependencies
[]

## Conflicts
[]

## Metadata Warnings
['Missing class docstring; purpose inferred from class name/category.', 'ScrapedProfile dataclass reference not found for this tool.', 'SearchResult dataclass reference not found for this tool.']
