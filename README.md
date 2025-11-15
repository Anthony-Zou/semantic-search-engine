# 🧠 Simple RAG Knowledge Base

A full-stack Retrieval-Augmented Generation (RAG) application for building a semantic search knowledge base. This project demonstrates the complete RAG pipeline using FastAPI, MySQL, Redis, and Sentence Transformers.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Development](#development)
- [License](#license)

## 🎯 Overview

This is a simple yet complete RAG (Retrieval-Augmented Generation) system that allows you to:
- Upload text documents
- Automatically create semantic embeddings
- Search using natural language queries
- Get relevant results ranked by similarity

Perfect for learning RAG concepts and as a reference implementation!

## 🏗️ Architecture
┌─────────────────┐
│  Frontend (UI)  │
│   HTML/JS       │
└────────┬────────┘
│ HTTP
┌────────▼─────────┐
│  FastAPI Backend │
│  (Python 3.12)   │
└─────┬──────┬─────┘
│      │
│      └──────────┐
│                 │
┌─────▼──────┐   ┌──────▼─────┐
│   MySQL    │   │   Redis    │
│ (Metadata) │   │ (Vectors)  │
└────────────┘   └────────────┘
## ✨ Features

- **Document Management**: Add, list, and delete documents
- **Semantic Search**: Natural language queries with cosine similarity
- **Vector Embeddings**: Using SentenceTransformers (all-MiniLM-L6-v2)
- **Dual Storage**: MySQL for structured data, Redis for vector embeddings
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Simple UI**: Clean HTML/JavaScript frontend
- **Jupyter Integration**: Experiment and analyze in notebooks
- **Dockerized**: Everything runs in containers

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SentenceTransformers (embeddings)
- PyMySQL (MySQL driver)
- Redis-py (Redis client)

**Databases:**
- MySQL 8.0 (document storage)
- Redis 7 (vector embeddings)

**Frontend:**
- Vanilla HTML/CSS/JavaScript

**Development:**
- Docker & Docker Compose
- Jupyter Lab

## 📦 Prerequisites

- Docker Desktop installed
- Docker Compose installed
- 4GB+ RAM available
- Ports available: 8000, 3306, 6379, 8888

## 🚀 Quick Start

### 1. Clone the Repository
```bash
# RAG Agent Full-Stack Application

Full-stack application with MySQL, Redis, FastAPI backend, and Jupyter for experimentation.

## Stack
- **Backend:** FastAPI (Python 3.12)
- **Database:** MySQL 8.0
- **Cache/Vector Store:** Redis 7
- **Notebooks:** Jupyter Lab

## Quick Start
```bash
# Start all services
docker-compose up

# Access points:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Jupyter: http://localhost:8888
# - MySQL: localhost:3306
# - Redis: localhost:6379
```

## Services

### Backend (FastAPI)
- Port 8000
- Auto-reload enabled
- Connected to MySQL and Redis

### MySQL
- Port 3306
- Database: rag_db
- User: raguser
- Password: ragpassword

### Redis
- Port 6379
- Persistent storage enabled

### Jupyter
- Port 8888
- Pre-installed: pymysql, redis, langchain, openai, chromadb
