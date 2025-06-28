# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2025-06-28

### Added
- Added `base64_data` field to data URI extraction results for better compatibility
- Added `size` field to image data URI extraction results
- Improved error handling and consistency in data URI parsing

### Fixed
- Fixed handling of base64-encoded data in `parse_data_uri`
- Fixed mime type detection for image data URIs
- Fixed test cases for data URI extraction

## [0.1.6] - 2025-06-28

### Added
- Initial release of the xsl package
- Core functionality for XML/HTML/SVG file editing
- XPath and CSS selector support
- Command-line interface and HTTP server
