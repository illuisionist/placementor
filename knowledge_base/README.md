# PlaceMentor AI Knowledge Base

Place your documents here. The ingestor will recursively scan each subdirectory.

## Folder Structure

```
knowledge_base/
├── placement_policies/     → LPU placement rules, eligibility, calendar
├── company_jds/            → Job descriptions from companies
├── interview_experiences/  → Student-shared interview experiences
├── learning_resources/     → DSA notes, CS notes, aptitude material
└── lpu_brochures/          → LPU placement brochures, statistics
```

## Supported Formats
- PDF (.pdf)
- Word Documents (.docx)
- Text files (.txt)
- Markdown (.md)

## How to Ingest

```bash
# Ingest all documents in a folder
python -m rag.ingestor --dir knowledge_base/placement_policies --collection placement_policies

# Ingest a single file
python -m rag.ingestor --file knowledge_base/company_jds/amazon_sde.pdf --collection company_jds
```

## Collections
| Folder | Collection Name |
|---|---|
| placement_policies | placement_policies |
| company_jds | company_jds |
| interview_experiences | interview_experiences |
| learning_resources | learning_resources |
| lpu_brochures | general |
