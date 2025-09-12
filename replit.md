# Overview

This is an AI-powered chatbot platform built with Flask that provides multi-language support and integrates with Google's Gemini AI. The platform features user authentication, admin management, and a knowledge base system where users can upload documents to enhance AI responses. It's designed for deployment on Replit with a focus on simplicity and accessibility.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **Flask 3.0.3** serves as the core web framework with blueprints for route organization
- **SQLAlchemy** provides ORM capabilities with SQLite as the default database
- **Flask-Login** handles user session management and authentication
- **Flask-Babel** enables internationalization with support for Uzbek, Russian, and English

## Authentication & Authorization
- Password-based authentication with hashed storage using Werkzeug
- Role-based access control with admin and regular user distinctions
- Trial period system (3 days) with paid user upgrades
- Admin approval workflow for new user registrations

## AI Integration
- **Google Gemini API** (gemini-pro model) powers the conversational AI
- Context-aware responses that incorporate uploaded knowledge base content
- Dynamic prompt construction combining user queries with knowledge base data

## Knowledge Management
- File upload system supporting TXT and PDF formats
- Secure file storage outside the static directory
- Knowledge base content automatically included in AI prompt context

## Frontend Architecture
- **Bootstrap 5** provides responsive UI components
- **Font Awesome** icons for visual enhancement
- **Chart.js** for potential analytics and data visualization
- Mobile-optimized design with progressive enhancement

## Security Features
- CSRF protection using session-based tokens for admin actions
- Secure filename handling for uploads
- Environment variable validation for production deployments
- File size limits (16MB) and type restrictions

## Multi-language Support
- Session-based language switching between Uzbek, Russian, and English
- Internationalization ready with Flask-Babel infrastructure
- Default language set to Uzbek with fallback mechanisms

# External Dependencies

## AI Services
- **Google Generative AI (Gemini)** - Primary AI conversation engine requiring GEMINI_API_KEY

## Frontend Libraries (CDN)
- **Bootstrap 5.3.0** - UI framework for responsive design
- **Font Awesome 6.0.0** - Icon library for enhanced user interface
- **Chart.js** - JavaScript charting library for data visualization

## Python Packages
- **Flask ecosystem** - Web framework, SQLAlchemy ORM, Login management, Babel i18n
- **Google Generative AI** - Official Gemini API client library
- **APScheduler** - Task scheduling capabilities
- **Gunicorn** - WSGI HTTP server for production deployment
- **python-dotenv** - Environment variable management

## Development & Deployment
- **Replit hosting platform** - Configured for port 5000 deployment
- **SQLite database** - File-based database suitable for development and small-scale production
- **Environment variables** - Secure configuration management for API keys and secrets