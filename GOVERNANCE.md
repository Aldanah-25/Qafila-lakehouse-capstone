# Data Governance and PII

## Data classification
The synthetic Qafila dataset may include:
- Customer names and contact information
- Mobile numbers
- National identifiers
- Bank account identifiers such as IBAN

These fields are classified as sensitive personal information.

## Required controls
- Do not publish raw customer databases to GitHub.
- Restrict access to raw and bronze layers.
- Mask or pseudonymize identifiers before exposing analytics tables.
- Avoid logging personal identifiers.
- Retain only fields needed for analytics.

## Current implementation status
This file documents the required controls.
It does not claim that all PII fields are technically masked.
The source data is synthetic.
