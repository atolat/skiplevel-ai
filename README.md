# skiplevel

**skiplevel** is an AI-powered growth system for engineers who are tired of waiting for their manager to notice them.

---

### Why this exists

> Engineers don't need performance reviews.  
> They need a mirror, a map, and a little less bullshit.

Let's be real:
- Promotions are political.
- Performance reviews are vague, biased, and retroactive.
- Good managers are rare. Bad ones are calendar-sitters who can't remember what you worked on.
- Your career shouldn't hinge on whether your manager had a good night's sleep before your performance review.

So we're building something else.

This is not:
- A performance review tool  
- A journal  
- A fancy OKR dashboard  

It's your career's **version control system**—without the gatekeepers.

---

### What skiplevel stands for

🔥 **Built for:**
- Engineers who are good at their jobs but bad at self-promotion
- ICs tired of "being more visible"
- People who want to grow through impact, not politics

💡 **Beliefs:**
- **Impact > Optics**  
- **Growth > Vibes**  
- **Truth > Perception**

🚫 **No babysitters. No gatekeepers. No emotional roulette.**

You've leveled up enough. Now it's time to **skip one**.

---

### Getting Started

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run the system:
   ```bash
   python -m skiplevel
   ```

For detailed technical documentation, see the [docs](docs/README.md) directory.

---

### Technical Architecture

The system is built using a multi-agent supervisor pattern with the following components:

#### Core Components
- `core/base.py`: Base tool interface and protocols
- `core/teams.py`: Team and agent definitions
- `core/supervisor.py`: Supervisor implementations
- `core/state.py`: State management

#### Teams
1. **Document Processing Team**
   - Document Ingestor
   - Document Parser
   - Document Storage Manager

2. **Analysis Team**
   - Content Analyzer
   - Pattern Detector
   - Insight Generator

3. **Advice Team**
   - Career Path Analyzer
   - Risk Assessor
   - Advice Formulator

4. **Vector DB Team**
   - Vector DB Manager
   - Embedding Generator
   - Query Optimizer

#### Directory Structure
```
.
├── core/               # Core system components
├── tools/             # Tool implementations
│   ├── document/      # Document processing tools
│   ├── analysis/      # Analysis tools
│   ├── advice/        # Advice generation tools
│   └── vectordb/      # Vector DB tools
├── agents/            # Agent implementations
│   ├── document/      # Document processing agents
│   ├── analysis/      # Analysis agents
│   ├── advice/        # Advice generation agents
│   └── vectordb/      # Vector DB agents
└── tests/             # Test suite
```

---

### Development

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run tests:
   ```bash
   pytest
   ```

---

### Contact

Built solo by [@atolat](https://github.com/atolat)  
Fueled by caffeine, clarity, and the deep desire to never hear "let's sync on this" again.
