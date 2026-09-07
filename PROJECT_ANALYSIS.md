# Crawler Project Analysis & Comparison with Problem Statement 5

## 🔍 Current Project Overview: TruthShield AI

### Project Name

**TruthShield AI** - A Multi-Agent Fact-Checking Assistant System

### Current Architecture

```
User Input (News Article / Text)
    ↓
[Claim Extractor Agent] → Extract verifiable claims
    ↓
[Fact Planner Agent] → Plan verification searches
    ↓
[Evidence Searcher Agent] → Search web via DuckDuckGo
    ↓
[Verdict Agent] → Generate fact-check verdicts
    ↓
Fact-Check Report (with accuracy scores & confidence levels)
```

### Tech Stack

**Backend:**

- FastAPI (Web Framework)
- Pydantic-AI (Multi-agent orchestration)
- SQLAlchemy (Database ORM)
- Anthropic/Cohere APIs (LLM)
- DuckDuckGo API (Web search)
- PyTorch & Transformers (ML models)

**Frontend:**

- React 19
- Simple dashboard UI
- Token-based authentication

**Database:**

- SQLAlchemy with user history tracking
- User authentication system

### Key Components

#### 1. **Backend Agents (fact_checker/)**

- `claim_extractor_agent.py` - Extracts verifiable claims from text
- `evidence_agent.py` - Plans searches and gathers evidence
- `verdict_generator.py` - Generates final fact-check verdicts
- `fact_checker_orchestrator.py` - Coordinates all agents

#### 2. **API Routes (routers/)**

- `/auth/register` - User registration
- `/auth/login` - User authentication
- `/detect/analyze` - Fact-checking endpoint
- `/chat/` - Chat interface (placeholder)

#### 3. **Services (services/)**

- `fact_checker_service.py` - Async/sync wrapper for fact-checking
- `email_service.py` - User notifications

#### 4. **Frontend Components (frontend/src/)**

- `Auth.js` - Login/Registration
- `Dashboard.js` - Main UI with text input & analysis
- `Result.js` - Display fact-check results

### Current Capabilities ✅

- Extract claims from text
- Search evidence via DuckDuckGo
- Generate structured verdicts
- Calculate accuracy scores
- User authentication & history
- Responsive React UI
- Async multi-agent orchestration

---

## 📋 Problem Statement 5: Intelligent Web Crawler & Action-Oriented Answer Agent

### Expected Capabilities

| Capability             | Description                                                 |
| ---------------------- | ----------------------------------------------------------- |
| **Web Crawling**       | Crawl/search the web based on natural-language user query   |
| **Relevance Ranking**  | Identify and rank the most relevant sites and sources       |
| **Content Extraction** | Extract and summarize relevant content                      |
| **Citations**          | Provide references/links back to source sites               |
| **Intent Detection**   | Detect actionable intent (jobs, products, events, services) |
| **Action Guidance**    | For jobs: surface listings & prompt user to apply           |

### Example Use Cases

1. **Query**: "Find me remote Python developer jobs posted this week"
   - **Expected Output**:
     - 5 relevant job postings
     - Summary (title, company, location, salary)
     - Direct links
     - Prompt: "Would you like to apply for Senior Python Developer role at Acme?"

2. **Query**: "What's the best budget mechanical keyboard right now?"
   - **Expected Output**:
     - Ranked review sites
     - Summarized recommendations
     - Cited sources

### Expected Deliverables

- End-to-end prototype (crawler + answer agent)
- Demonstration across at least one actionable use case (e.g., jobs)
- Architecture documentation
- Explanation of crawling, ranking, and action-detection approach

---

## 🔄 Comparison: TruthShield AI vs Problem Statement 5

### ✅ SIMILARITIES

| Feature                    | TruthShield      | Problem Statement | Status   |
| -------------------------- | ---------------- | ----------------- | -------- |
| **Multi-Agent System**     | Yes (4 agents)   | Yes               | ✅ Match |
| **Web Search Integration** | Yes (DuckDuckGo) | Yes (required)    | ✅ Match |
| **Evidence Gathering**     | Yes              | Yes               | ✅ Match |
| **API/FastAPI Backend**    | Yes              | Yes               | ✅ Match |
| **User Interface**         | Yes (React)      | Yes               | ✅ Match |
| **NLP Processing**         | Yes              | Yes               | ✅ Match |

### ❌ CRITICAL GAPS

| Feature                         | TruthShield           | Problem Statement     | Gap            |
| ------------------------------- | --------------------- | --------------------- | -------------- |
| **Web Crawling**                | ❌ No crawler         | ✅ Required           | 🔴 **MISSING** |
| **Actionable Intent Detection** | ❌ No                 | ✅ Required           | 🔴 **MISSING** |
| **Job Listing Extraction**      | ❌ No                 | ✅ Required (example) | 🔴 **MISSING** |
| **Apply Assistance**            | ❌ No                 | ✅ Required           | 🔴 **MISSING** |
| **Site Ranking Algorithm**      | ❌ No                 | ✅ Required           | 🔴 **MISSING** |
| **General Q&A**                 | ❌ Fact-checking only | ✅ Required           | 🔴 **MISSING** |
| **Citation Management**         | ⚠️ Partial            | ✅ Required           | 🟡 **Partial** |
| **Answer Summarization**        | ⚠️ Partial            | ✅ Required           | 🟡 **Partial** |

---

## 📊 Detailed Gap Analysis

### 1. **Web Crawling** 🔴

**Current State**: None
**Needed**: Actual web crawler to fetch and parse HTML/content from websites

**Missing Components**:

- Web scraper (BeautifulSoup, Selenium, or Scrapy)
- URL discovery algorithm
- Content parser
- Duplicate detection
- Rate limiting & respectful crawling

### 2. **Actionable Intent Detection** 🔴

**Current State**: Only fact-checking verdicts
**Needed**: Classification of user intent into categories

**Missing Components**:

- Intent classifier (Jobs, Products, Events, Services, etc.)
- Intent-specific handlers
- Domain-specific parsers

### 3. **Job Board Integration** 🔴

**Current State**: None
**Needed**: Search and extract job listings

**Missing Components**:

- Job board APIs/scrapers (LinkedIn, Indeed, Glassdoor, etc.)
- Job listing parser
- Job matching algorithm
- Application workflow integration

### 4. **Site Relevance Ranking** 🔴

**Current State**: Basic search ordering from DuckDuckGo
**Needed**: Custom ranking algorithm

**Missing Components**:

- TF-IDF or BM25 scoring
- PageRank-like algorithm
- Domain authority scoring
- Freshness scoring
- Relevance scoring

### 5. **Action Guidance System** 🔴

**Current State**: Only analysis/reporting
**Needed**: Interactive prompts and action assistance

**Missing Components**:

- Action confirmation prompts
- Application form filling assistance
- Booking/registration helpers
- Event calendar integration

### 6. **General Q&A Mode** 🔴

**Current State**: Fact-checking pipeline only
**Needed**: Answer agent for general queries

**Missing Components**:

- Answer generation agent
- Query understanding
- Multi-source synthesis
- Answer quality scoring

---

## 🚀 Implementation Roadmap

### Phase 1: Web Crawler Foundation (Week 1-2)

```python
# IMPLEMENT:
1. Web Crawler Module
   - BeautifulSoup/Scrapy for HTML parsing
   - URL queue management
   - Content extraction
   - Rate limiting & robots.txt respect

2. Search Integration
   - Integrate multiple search APIs (Google, Bing, DuckDuckGo)
   - URL preprocessing
   - Duplicate detection

DELIVERABLE: crawler_module.py with CrawlerAgent
```

### Phase 2: Intent Detection (Week 2-3)

```python
# IMPLEMENT:
1. Intent Classifier
   - Train/use model to classify user intent
   - Categories: GENERAL, JOBS, PRODUCTS, EVENTS, SERVICES
   - Confidence scoring

2. Intent-Specific Handlers
   - JobHandler
   - ProductHandler
   - EventHandler
   - GeneralHandler

DELIVERABLE: intent_detection/ module with agents
```

### Phase 3: Ranking Algorithm (Week 3)

```python
# IMPLEMENT:
1. Relevance Scorer
   - TF-IDF/BM25 implementation
   - Domain authority scoring
   - Freshness calculation
   - Combined ranking

2. Result Sorter
   - Sort search results by score
   - Deduplication
   - Quality filtering

DELIVERABLE: ranking_engine.py
```

### Phase 4: Job Listing Pipeline (Week 4)

```python
# IMPLEMENT:
1. Job Board Integration
   - Job scraper for major platforms
   - Listing parser
   - Skill matching

2. Application Workflow
   - Job recommendation engine
   - Application prompt generation
   - Application tracking

DELIVERABLE: job_pipeline/ module
```

### Phase 5: Answer Agent & UI (Week 4-5)

```python
# IMPLEMENT:
1. Answer Agent
   - Multi-source synthesis
   - Citation formatting
   - Confidence scoring

2. Frontend Enhancements
   - Query input instead of text paste
   - Result display improvements
   - Action buttons (Apply, Visit, etc.)
   - Intent visualization

DELIVERABLE: answer_agent.py + updated UI
```

---

## 📝 To-Do List: Implementation Tasks

### PRIORITY: HIGH 🔴

- [ ] **Web Crawler Development**
  - [ ] Build URL discovery module
  - [ ] Implement HTML parser (BeautifulSoup)
  - [ ] Add rate limiting & robots.txt support
  - [ ] Test crawler on sample websites
- [ ] **Intent Classification System**
  - [ ] Define intent categories
  - [ ] Create intent classifier agent
  - [ ] Add confidence scoring
  - [ ] Test with sample queries

- [ ] **Site Ranking Algorithm**
  - [ ] Implement TF-IDF scoring
  - [ ] Add domain authority scoring
  - [ ] Create combined ranking
  - [ ] Benchmark against baselines

### PRIORITY: MEDIUM 🟡

- [ ] **Job Pipeline Development**
  - [ ] Create job scraper module
  - [ ] Implement job parser
  - [ ] Add job matching algorithm
  - [ ] Create job recommendation agent

- [ ] **Answer Generation**
  - [ ] Build multi-source synthesis agent
  - [ ] Implement citation formatter
  - [ ] Add confidence scoring
  - [ ] Create summary generator

- [ ] **UI Improvements**
  - [ ] Change from text paste to query input
  - [ ] Add result cards with sources
  - [ ] Implement action buttons
  - [ ] Add loading states

### PRIORITY: LOW 🟢

- [ ] **Additional Intent Handlers**
  - [ ] Product search & ranking
  - [ ] Event finder
  - [ ] Service locator
  - [ ] Price comparison

- [ ] **Advanced Features**
  - [ ] Caching & indexing
  - [ ] User preferences
  - [ ] Search history
  - [ ] Result feedback loop

---

## 🏗️ Architecture Changes Needed

### Current Architecture

```
User Input → Claim Extraction → Evidence Search → Verdict → Report
```

### Proposed New Architecture

```
User Query
    ↓
[Query Parser] → Extract intent & keywords
    ↓
[Intent Classifier] → Categorize (Jobs/Products/General/etc.)
    ↓
[URL Searcher] → Find relevant URLs
    ↓
[Web Crawler] → Fetch & parse content
    ↓
[Ranker] → Score & sort results
    ↓
[Answer Agent] → Synthesize answer
    ↓
[Action Handler] → Detect & execute actionable intents
    ↓
[UI Formatter] → Display with citations & action buttons
```

---

## 📦 New Dependencies to Add

```txt
# Web Crawling
beautifulsoup4>=4.12.0
scrapy>=2.11.0
selenium>=4.15.0
lxml>=4.9.0

# Ranking
scikit-learn>=1.3.0
numpy>=1.24.0

# Job Processing
linkedin-api>=0.2.0
indeed-scraper>=0.1.0

# Additional Search
google-search-results>=2.4.0
bing-image-downloader>=1.7.11

# Utilities
feedparser>=6.0.0
langdetect>=1.0.9
```

---

## ✅ What's Already Good

1. **Multi-Agent Orchestration**: TruthShield's FactChecker can be adapted for this use case
2. **FastAPI Backend**: Solid foundation for new endpoints
3. **React UI**: Can be enhanced with new components
4. **Authentication**: Already implemented
5. **Database Schema**: Can store search history & results
6. **Error Handling**: Fallback mechanisms in place

---

## 📋 Summary: Similarity Score

| Aspect                 | Match % |
| ---------------------- | ------- |
| Architecture Approach  | 70%     |
| Agent Pattern          | 80%     |
| Backend Stack          | 75%     |
| Frontend Setup         | 60%     |
| Core Functionality     | 30%     |
| **Overall Similarity** | **53%** |

**Verdict**: TruthShield has the **architecture and infrastructure** needed but lacks the **core crawler and action-oriented capabilities** of Problem Statement 5.

---

## 🎯 Recommendation

**Pivot TruthShield into a General-Purpose Answer Agent**:

1. Keep the multi-agent orchestration pattern
2. Add web crawler module
3. Implement intent classification
4. Build ranking algorithm
5. Create action handlers for specific domains
6. Update UI for query-based interaction

This would create **"SearchShield AI"** - combining fact-checking credibility with web crawling and actionable insights.
