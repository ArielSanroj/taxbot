# TaxBot Enterprise

Enterprise-grade DIAN concepts scraper and analyzer with AI-powered insights.

## Features

- 🔍 **Automated Scraping**: Daily extraction of DIAN concepts and legal documents
- 🤖 **AI Analysis**: Ollama integration for intelligent summarization and analysis
- 🌐 **REST API**: FastAPI-based web service for on-demand queries
- 📧 **Smart Notifications**: Email alerts for new concepts with summaries
- 🐳 **Docker Ready**: Containerized deployment with Ollama integration
- 🔒 **Production Security**: JWT authentication, input validation, rate limiting
- 📊 **Monitoring**: Health checks, metrics, structured logging
- 🧪 **Tested**: 80%+ test coverage with comprehensive test suite

## Prerequisites

- Python 3.10 or higher
- Ollama installed and running (for AI features)
- Git

### Ollama Setup

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Download the model**:
   ```bash
   ollama pull llama3
   ```

## Installation

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd taxbot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Docker Deployment

1. **Using Docker Compose** (recommended):
   ```bash
   docker-compose up -d
   ```

2. **Manual Docker build**:
   ```bash
   docker build -t taxbot .
   docker run -d --name taxbot -p 8000:8000 --env-file .env taxbot
   ```

## Configuration

Copy `.env.example` to `.env` and configure the following variables:

### Required Settings

- `OLLAMA_MODEL`: Ollama model to use (default: llama3)
- `DIAN_EMAIL_SENDER`: Email address for sending notifications
- `DIAN_EMAIL_PASSWORD`: Email password or app-specific password
- `DIAN_EMAIL_RECIPIENTS`: Comma-separated list of recipient emails

### Optional Settings

- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `SCRAPER_DELAY`: Delay between requests in seconds (default: 1.0)

## Usage

### Command Line Interface

```bash
# Run scraping pipeline
taxbot scrape

# Start API server
taxbot serve

# Check system status
taxbot status

# Get help
taxbot --help
```

### API Endpoints

Once the API server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Key Endpoints

- `GET /health` - System health check
- `GET /api/v1/concepts` - List concepts with pagination
- `GET /api/v1/concepts/{id}` - Get specific concept
- `POST /api/v1/concepts/search` - Full-text search
- `POST /api/v1/admin/scrape` - Trigger manual scraping

### Scheduled Automation

#### Unix/macOS (Cron)

```bash
# Add to crontab for daily execution at 6 AM
0 6 * * * /path/to/taxbot/scripts/setup_cron.sh
```

#### Windows (Task Scheduler)

```powershell
# Run the PowerShell script to set up scheduled task
.\scripts\setup_task.ps1
```

## Development

### Setup Development Environment

1. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

4. **Run linting**:
   ```bash
   ruff check .
   black .
   mypy .
   ```

### Project Structure

```
taxbot/
├── src/taxbot/           # Main source code
│   ├── core/             # Configuration and logging
│   ├── models/           # Domain models
│   ├── scrapers/         # Web scraping logic
│   ├── processors/       # AI processing
│   ├── storage/          # Data persistence
│   ├── notifications/    # Email services
│   ├── api/              # FastAPI application
│   └── cli/              # Command line interface
├── tests/                # Test suite
├── scripts/              # Deployment scripts
├── docs/                 # Documentation
└── data/                 # Data storage
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=taxbot --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration  # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

## API Documentation

### Authentication

Admin endpoints require API key authentication:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/admin/status
```

### Example API Calls

```bash
# Get all concepts
curl "http://localhost:8000/api/v1/concepts?limit=10&offset=0"

# Search concepts
curl -X POST "http://localhost:8000/api/v1/concepts/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "IVA", "limit": 5}'

# Trigger manual scraping
curl -X POST "http://localhost:8000/api/v1/admin/scrape" \
  -H "X-API-Key: your-api-key"
```

## Troubleshooting

### Common Issues

1. **Ollama not available**:
   - Ensure Ollama service is running: `ollama serve`
   - Check if model is downloaded: `ollama list`
   - Verify OLLAMA_BASE_URL in .env

2. **Email not sending**:
   - Check email credentials in .env
   - Verify SMTP settings
   - Test with a simple email client

3. **Scraping fails**:
   - Check network connectivity
   - Verify target website is accessible
   - Review logs for specific errors

4. **API not starting**:
   - Check if port 8000 is available
   - Verify all dependencies are installed
   - Review configuration in .env

### Logs

- **Application logs**: `data/dian_pipeline.log`
- **API logs**: Console output or configured log files
- **Docker logs**: `docker logs taxbot`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `ruff check . && black . && mypy .`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation at `/docs`

## Roadmap

- [ ] SQLite/PostgreSQL database support
- [ ] Web dashboard interface
- [ ] Multi-source scraping
- [ ] Advanced analytics and reporting
- [ ] Slack/Teams notifications
- [ ] Kubernetes deployment manifests
