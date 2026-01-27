# Educmad PDF

## Overview

Educmad PDF is a web service that scrapes educational content from the EducMad website (a Malagasy educational platform) and converts it to PDF format. The application provides an API that allows users to fetch course materials by subject and academic series (A, C, D, L, S, OSE), then generates downloadable PDF documents from the scraped content.

The supported subjects include:
- Physics (Physique)
- Mathematics (Maths)
- Life and Earth Sciences (SVT)
- History-Geography (HG)
- Philosophy (Philo)
- Malagasy Language

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask** serves as the lightweight web framework
- Designed as a simple API service with minimal routing
- Configured for deployment on Vercel's serverless platform

### Content Scraping
- **Requests** library handles HTTP requests to the EducMad website
- **BeautifulSoup4** parses HTML content from scraped pages
- Course IDs are pre-mapped in a dictionary structure organized by subject and series

### PDF Generation
- **WeasyPrint** converts HTML content to PDF format
- PDFs are generated in-memory using io streams for efficient handling
- No persistent file storage required

### Data Structure
- Course mapping uses a nested dictionary pattern: `COURSE_MAP[subject][series] = course_id`
- This allows quick lookup of EducMad course IDs based on user requests

### Deployment Architecture
- Configured for Vercel serverless deployment via `vercel.json`
- All routes are directed to the main Flask application
- Stateless design suitable for serverless execution

## External Dependencies

### Third-Party Services
- **EducMad Website**: Primary data source for educational content (scraping target)

### Python Packages
| Package | Purpose |
|---------|---------|
| Flask | Web framework and API routing |
| requests | HTTP client for web scraping |
| beautifulsoup4 | HTML parsing and content extraction |
| weasyprint | HTML to PDF conversion |

### Deployment Platform
- **Vercel**: Serverless hosting platform with Python runtime support

### System Requirements
- WeasyPrint requires system-level dependencies (Cairo, Pango, GDK-PixBuf) which may need to be installed on the deployment environment