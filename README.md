# Patent Automation System

A comprehensive CrewAI-based system for automating patent application generation and portfolio management.

## 🏗️ Project Structure

```
method-patent/
├── config/                 # YAML configuration files
│   ├── agents.yaml        # Agent definitions and tool mappings
│   ├── tasks.yaml         # Task definitions with output_pydantic
│   ├── crew.yaml          # Crew configuration
│   └── patents.yaml       # All 37 patents in structured format
├── core/                  # Core system modules
│   ├── patent_data.py     # Patent database (37 patents)
│   ├── automation.py      # Automation logic
│   ├── validation.py      # Data validation utilities
│   ├── utils.py           # General utilities
│   └── export.py          # Export functionality
├── tools/                 # CrewAI tools
│   ├── patent_document.py
│   ├── patent_valuation.py
│   ├── real_patent_search.py
│   ├── arxiv_search.py
│   ├── smart_claim_refinement.py
│   ├── final_review_and_improvement.py
│   ├── provisional_cover_sheet.py
│   ├── enhanced_prior_art_search.py
│   ├── consolidated_risk_assessment.py
│   ├── vector_based_overlap_analysis.py
│   └── colab_demo_generator.py
├── docs/                  # Documentation
│   ├── patent_list.md     # Original patent list (37 patents)
│   └── patent_strategy_2025.md
├── tests/                 # Test files
│   └── test_valuation.py
├── scripts/               # Utility scripts
│   └── cleanup_tools.py
├── patent_output/         # Generated patent documents
│   ├── tier_1/
│   ├── tier_2/
│   ├── tier_3/
│   └── colab_demos/
├── vector_cache/          # Vector analysis cache
├── run_patent_automation.py  # Main runner script
├── requirements.txt       # Python dependencies
└── .gitignore
```

## 🎯 Key Features

- **37 Patents**: Comprehensive portfolio across 3 tiers
- **CrewAI Native**: Uses YAML configuration for agents, tasks, and crews
- **Pydantic Validation**: Structured input/output validation
- **Multi-Tier Processing**: Tier 1 (2), Tier 2 (22), Tier 3 (13)
- **Automated Generation**: Prior art search, claims refinement, legal review

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY="your-key"
   export LANGCHAIN_API_KEY="your-langsmith-key"  # Optional: for LangSmith monitoring
   export LENS_API_KEY="your-key"  # Optional
   export EPO_API_KEY="your-key"   # Optional
   ```

3. **Check system status** (recommended):
   ```bash
   python scripts/manage_context.py --status
   ```

4. **Check incremental processing status**:
   ```bash
   python scripts/incremental_manager.py --status
   ```

5. **Run automation** (incremental by default):
   ```bash
   python run_patent_automation.py
   ```

## 🔧 Troubleshooting

### Context Size Issues
If you encounter context length errors:
```bash
# Clear cache and outputs
python scripts/manage_context.py --clear-all

# Analyze context impact
python scripts/manage_context.py --analyze

# Run with cache clearing disabled (use with caution)
python run_patent_automation.py --no-clear-cache
```

### OpenAI Quota Issues
- Check your OpenAI billing at https://platform.openai.com/account/billing
- Ensure you have sufficient credits for the model you're using
- Consider using `gpt-4o-mini` for testing to reduce costs

### Model Configuration
The system now uses `gpt-4o` by default (128k token limit). To change models:
- Set environment variable: `export OPENAI_MODEL=gpt-4o-mini`
- Or modify `config/agents.yaml` to specify different models per agent

### Incremental Processing
The system now supports incremental processing to avoid recreating existing assets:

1. **Check asset status**:
   ```bash
   python scripts/incremental_manager.py --status
   ```

2. **Show only missing assets**:
   ```bash
   python scripts/incremental_manager.py --missing-only
   ```

3. **Show task completion statistics**:
   ```bash
   python scripts/incremental_manager.py --task-stats
   ```

4. **Force regenerate specific asset**:
   ```bash
   python scripts/incremental_manager.py --force-regenerate patent_001 colab_demo_generation
   ```

5. **Force regenerate all assets**:
   ```bash
   python scripts/incremental_manager.py --force-regenerate-all
   ```

6. **Run with incremental processing disabled**:
   ```bash
   python run_patent_automation.py --no-incremental
   ```

7. **Run with force regeneration**:
   ```bash
   python run_patent_automation.py --force-regenerate
   ```

### Incremental Processing Features
- **Smart asset detection**: Automatically detects existing, valid output files
- **File validation**: Validates file size, format, and content quality
- **Selective execution**: Only runs tasks for missing or invalid assets
- **Force regeneration**: Can force regeneration of specific or all assets
- **Completion tracking**: Tracks completion percentage per patent and task type
- **Status reporting**: Comprehensive reports on what exists vs. what's missing

### Tool Execution Failures
The system now includes comprehensive retry and recovery mechanisms:

1. **Check failed executions**:
   ```bash
   python scripts/recovery_manager.py --show-failed
   ```

2. **View execution summary**:
   ```bash
   python scripts/recovery_manager.py --show-summary
   ```

3. **Reset failed executions for retry**:
   ```bash
   python scripts/recovery_manager.py --reset-failed
   ```

4. **Generate recovery report**:
   ```bash
   python scripts/recovery_manager.py --report
   ```

5. **Reset specific patent or tool**:
   ```bash
   python scripts/recovery_manager.py --reset-patent "patent_001"
   python scripts/recovery_manager.py --reset-tool "real_patent_search_tool"
   ```

### Recovery Features
- **Automatic retries**: Tools automatically retry up to 3 times with exponential backoff
- **Fallback results**: When tools fail completely, the system provides fallback analysis
- **Persistent tracking**: All execution attempts are tracked and persisted
- **Recovery reports**: Comprehensive reports on failures and recommendations
- **Selective reset**: Reset specific failed executions for targeted recovery

## 📊 Patent Portfolio

- **Total**: 37 patents (as defined in patent_list.md)
- **Estimated Value**: $150M - $900M
- **Tier 1**: 2 patents (Healthcare/Financial - $6-20M each)
- **Tier 2**: 22 patents (Core technologies - $4-15M each)
- **Tier 3**: 13 patents (Applications - $3-12M each)

## 🔍 LangSmith Monitoring (Optional)

The system includes optional LangSmith integration for debugging, testing, and monitoring LLM applications.

### Setup LangSmith

1. **Get a LangSmith API key**:
   - Sign up at https://smith.langchain.com/
   - Get your API key from the dashboard

2. **Set the environment variable**:
   ```bash
   export LANGCHAIN_API_KEY="your-langsmith-api-key"
   ```

3. **Run the demo** to test LangSmith integration:
   ```bash
   python scripts/langsmith_demo.py
   ```

### LangSmith Features

- **Function Tracing**: Use `@trace_function` decorator to trace any function
- **Agent Monitoring**: Automatic logging of agent executions
- **Tool Monitoring**: Track tool usage and performance
- **Debugging**: Detailed traces for troubleshooting
- **Performance Analysis**: Monitor response times and token usage

### Configuration

LangSmith settings can be configured in `config/langsmith_config.yaml`:
- Project name and tags
- Sampling rates
- Metadata and environment settings
- Tracing verbosity

### Usage Examples

```python
from core.langsmith_utils import trace_function, log_agent_execution

@trace_function(name="my_function")
def my_function():
    # This function will be traced in LangSmith
    pass

# Log agent execution
log_agent_execution("agent_name", "task_name", inputs, outputs)
```

## 🔧 Configuration

All configuration is YAML-based in the `config/` directory:

- **`agents.yaml`**: Define agents with roles, goals, and tools
- **`tasks.yaml`**: Define tasks with descriptions and output validation
- **`crew.yaml`**: Define crew workflows
- **`patents.yaml`**: Structured patent data

## 🛠️ Development

- **Tools**: Add new tools to `tools/` directory
- **Configuration**: Modify YAML files in `config/`
- **Patents**: Update `core/patent_data.py` or `config/patents.yaml`
- **Tests**: Add tests to `tests/` directory

## 📈 Output

Generated documents are saved to `patent_output/` organized by tiers:
- Prior art analysis
- Refined claims
- Patent applications
- Legal reviews
- Cover sheets

## 🎉 Benefits

- **Structured**: Clean, organized codebase
- **Scalable**: Easy to add new patents and tools
- **Maintainable**: Clear separation of concerns
- **Configurable**: YAML-driven configuration
- **Validated**: Pydantic input/output validation 