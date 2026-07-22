# Metadata Folder Documentation

This folder contains metadata files that describe and index all documents in the dataset repository.

## Files

### metadata.csv
Complete metadata for all classified documents.

| Column | Description |
|--------|-------------|
| Filename | Original filename |
| DocumentType | Classification type (RFI, Equipment_Specification, Commissioning, etc.) |
| Equipment | Equipment category (UPS, Generator, ATS/Switchgear, etc.) |
| Vendor | Vendor/Manufacturer name |
| Category | Parent category folder |
| Extension | File extension |
| Pages | Number of pages (N/A if not applicable) |
| SourceFolder | Original source folder |
| DestinationFolder | Organized destination folder |

### file_index.csv
Complete index of all files in the dataset repository.

| Column | Description |
|--------|-------------|
| Filename | File name |
| Extension | File extension |
| Size_KB | File size in kilobytes |
| RelativePath | Relative path from datasets folder |
| LastModified | Last modification timestamp |

### duplicates.csv
Log of duplicate files detected during organization.

| Column | Description |
|--------|-------------|
| Filename | Duplicate filename |
| OriginalSource | Path to original file |
| DuplicateSource | Path to duplicate file |
| Status | Action taken |

## Document Classification Summary

| Document Type | Count | Description |
|---------------|-------|-------------|
| RFI | 13 | Requests for Information |
| Equipment_Specification | 7 | Equipment technical specifications |
| Commissioning | 2 | Commissioning procedures and tests |
| Research_Paper | 7 | White papers and research documents |
| Unclassified | 7 | Documents requiring manual classification |
| Web_Asset | 112 | Web resources (CSS, JS, HTML) |

## Classification Rules Applied

- **RFI Keywords**: "RFI", "Request for Information", "Questions and Answers"
- **UPS Equipment**: "UPS", "Uninterruptible Power Supply", "ABB", "Eaton"
- **Generator Equipment**: "Generator", "Standby", "LEBW"
- **Commissioning**: "commissioning", "startup", "test procedure", "acceptance"
- **White Papers**: "white paper", "whitepaper"

## Notes

- Original files preserved in source location
- Files copied (not moved) to maintain data integrity
- Duplicate files logged but not copied twice
- Web assets from Scribd saved page isolated in 15_Web_Assets

---
*Last Updated: 2026-06-29*
