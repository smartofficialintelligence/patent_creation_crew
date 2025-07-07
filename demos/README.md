# Patent Pipeline Demos

This directory contains demonstration scripts that showcase the various features and capabilities of the patent automation system.

## Available Demos

### 1. Agent-Aware Optimization Demo
**File:** `demo_agent_aware_optimization.py`
**Description:** Demonstrates how the system preserves your thoughtfully selected agent models while achieving cost optimization through non-model optimizations.

**Key Features:**
- Shows agent model preservation (100% preservation rate)
- Demonstrates cost reduction through context optimization
- Illustrates agent-specific optimization strategies
- Provides detailed cost breakdown analysis

**Usage:**
```bash
python demos/demo_agent_aware_optimization.py
```

### 2. Dynamic Optimization Demo
**File:** `demo_dynamic_optimization.py`
**Description:** Showcases the dynamic resource optimization system that adapts to task complexity and resource availability.

**Key Features:**
- Dynamic model selection based on task complexity
- Intelligent token allocation and budgeting
- Context optimization with dynamic truncation
- Real-time resource monitoring and cost tracking

**Usage:**
```bash
python demos/demo_dynamic_optimization.py
```

### 3. Quality Validation Demo
**File:** `demo_quality_validation.py`
**Description:** Demonstrates the comprehensive quality validation pipeline that ensures high-quality patent outputs.

**Key Features:**
- Multi-tier quality validation (quick, standard, thorough)
- Semantic content validation
- Document structure verification
- Quality score calculation and reporting

**Usage:**
```bash
python demos/demo_quality_validation.py
```

### 4. Parallel Execution Demo
**File:** `demo_parallel_execution.py`
**Description:** Shows how the parallel execution system coordinates multiple tasks while maintaining quality and efficiency.

**Key Features:**
- Task dependency management
- Parallel execution with resource limits
- Performance comparison (sequential vs parallel)
- Resource usage monitoring

**Usage:**
```bash
python demos/demo_parallel_execution.py
```

## Running Demos

### Prerequisites
Make sure you have the patent pipeline environment set up:
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running Individual Demos
Each demo can be run independently:
```bash
# From the project root
python demos/demo_agent_aware_optimization.py
python demos/demo_dynamic_optimization.py
python demos/demo_quality_validation.py
python demos/demo_parallel_execution.py
```

### Running All Demos
To run all demos in sequence:
```bash
# From the project root
for demo in demos/demo_*.py; do
    echo "Running $demo..."
    python "$demo"
    echo "Completed $demo"
    echo "---"
done
```

## Demo Output

Each demo generates:
- Console output showing the feature in action
- Performance metrics and statistics
- Example results and analysis
- Detailed explanations of what's happening

## Understanding the Results

### Agent-Aware Optimization
- **Model Preservation**: Shows which agents keep their original models
- **Cost Reduction**: Demonstrates savings through context optimization
- **Quality Maintenance**: Proves quality isn't compromised

### Dynamic Optimization
- **Adaptive Behavior**: Shows how the system adapts to different scenarios
- **Resource Efficiency**: Demonstrates intelligent resource allocation
- **Cost Tracking**: Real-time cost monitoring and optimization

### Quality Validation
- **Validation Levels**: Different thoroughness levels for different needs
- **Quality Scores**: Numerical quality assessment
- **Issue Detection**: Identifies and reports quality issues

### Parallel Execution
- **Time Savings**: Compares sequential vs parallel execution times
- **Resource Usage**: Shows how resources are managed during parallel execution
- **Success Rates**: Demonstrates reliability of parallel processing

## Integration with Main System

These demos showcase features that are integrated into the main patent automation pipeline:

```bash
# Main system usage with optimizations
python run_patent_automation.py \
    --tier tier_1 \
    --max-per-tier 1 \
    --parallel --max-workers 5 \
    --optimization-level conservative \
    --validation-level thorough \
    --optimization-report
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root
2. **API Keys**: Ensure your `.env` file has the required API keys
3. **Dependencies**: Run `pip install -r requirements.txt` if you get import errors
4. **Memory Issues**: Some demos may require sufficient memory; adjust limits if needed

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your environment setup
3. Review the demo code for requirements
4. Check the main README.md for system requirements

## Contributing

When adding new demos:
1. Follow the naming convention: `demo_<feature_name>.py`
2. Add comprehensive docstrings and comments
3. Include example usage and expected output
4. Update this README with the new demo description
5. Test the demo independently to ensure it works 