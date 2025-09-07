# Zephyr Test Management MCP Server

A comprehensive MCP server for SmartBear Zephyr test management that provides detailed insights into test execution, defects, and release status.

## Features

🎯 **Comprehensive Test Management Insights:**
- Release status and execution summaries
- Regression test counts and tracking
- Negative test identification and counts
- Defect summaries by project/version
- Test execution progress monitoring
- Detailed execution reports
- Comprehensive test reporting

🔧 **Key Capabilities:**
- Multi-project support
- Version/release filtering
- Cycle-based test organization
- Real-time execution tracking
- Automated negative test detection
- Defect correlation with test results

## Installation

1. **Install Dependencies:**
```bash
pip install mcp aiohttp python-dotenv
```

2. **Set Environment Variables:**
Create a `.env` file or set these environment variables:

```bash
# Required: Zephyr instance URL
ZEPHYR_BASE_URL=https://your-instance.atlassian.net

# Authentication Method 1: Username/Password
ZEPHYR_USERNAME=your-username
ZEPHYR_PASSWORD=your-password

# Authentication Method 2: Access Token (alternative to username/password)
ZEPHYR_ACCESS_KEY=your-access-token
```

3. **Add to MCP Settings:**
Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "zephyr-test-management": {
      "command": "python",
      "args": ["/path/to/zephyr_mcp_server.py"],
      "env": {
        "ZEPHYR_BASE_URL": "https://your-instance.atlassian.net",
        "ZEPHYR_USERNAME": "your-username",
        "ZEPHYR_PASSWORD": "your-password"
      }
    }
  }
}
```

## Available Tools

### 🏢 Project Management
- **`get_projects`** - List all available projects
- **`get_release_status`** - Get comprehensive release status for a project

### 📊 Test Execution Analysis
- **`get_test_execution_summary`** - Get pass/fail counts and execution metrics
- **`get_execution_progress`** - Monitor test execution progress by cycle
- **`get_execution_details`** - Get detailed test execution information

### 🔍 Specialized Test Counts
- **`get_regression_test_count`** - Count and identify regression tests
- **`get_negative_test_count`** - Count and identify negative/error tests

### 🐛 Defect Management
- **`get_defect_summary`** - Get defect information by project/version

### 📈 Reporting
- **`generate_test_report`** - Generate comprehensive test reports

## Usage Examples

### Get All Projects
```python
# List all projects in your Zephyr instance
result = await call_tool("get_projects", {})
```

**Sample Output:**
```json
{
  "projects": [
    {
      "id": "10001",
      "key": "MYAPP",
      "name": "My Application",
      "description": "Main application project"
    }
  ],
  "total_count": 1,
  "timestamp": "2024-12-07T10:30:00"
}
```

### Get Release Status
```python
# Get comprehensive release status for a project
result = await call_tool("get_release_status", {
    "project_id": "10001",
    "version_id": "10100"  # Optional: specific version
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "releases": [
    {
      "version": {
        "id": "10100",
        "name": "v2.1.0",
        "description": "Major release"
      },
      "execution_summary": {
        "totalTestsCount": 450,
        "totalExecuted": 380,
        "totalPassed": 320,
        "totalFailed": 45,
        "totalBlocked": 15
      },
      "cycles": [...],
      "cycle_count": 5
    }
  ]
}
```

### Get Test Execution Summary
```python
# Get detailed execution metrics
result = await call_tool("get_test_execution_summary", {
    "project_id": "10001",
    "version_id": "10100"
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "execution_summary": {
    "totalTestsCount": 450,
    "totalExecuted": 380,
    "totalPassed": 320,
    "totalFailed": 45,
    "totalBlocked": 15,
    "executionRate": 84.4,
    "passRate": 71.1
  }
}
```

### Get Regression Test Count
```python
# Count regression tests in a specific version
result = await call_tool("get_regression_test_count", {
    "project_id": "10001",
    "version_id": "10100",
    "cycle_name": "regression"  # Optional filter
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "regression_cycles": [
    {
      "id": "101",
      "name": "Regression Suite",
      "description": "Full regression testing"
    }
  ],
  "total_regression_tests": 125
}
```

### Get Negative Test Count
```python
# Identify and count negative/error tests
result = await call_tool("get_negative_test_count", {
    "project_id": "10001",
    "version_id": "10100"
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "negative_test_count": 35,
  "negative_tests": [
    {
      "id": "12345",
      "testCaseName": "Login with invalid credentials",
      "executionStatus": "PASS"
    }
  ],
  "total_tests": 450
}
```

### Get Defect Summary
```python
# Get defects raised for a project/version
result = await call_tool("get_defect_summary", {
    "project_id": "10001",
    "version_id": "10100"
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "defect_summary": {
    "totalDefects": 23,
    "openDefects": 8,
    "resolvedDefects": 15,
    "criticalDefects": 2,
    "highPriorityDefects": 6
  }
}
```

### Get Execution Progress
```python
# Monitor test execution progress by cycle
result = await call_tool("get_execution_progress", {
    "project_id": "10001",
    "version_id": "10100",
    "cycle_id": "101"  # Optional: specific cycle
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "progress": [
    {
      "cycle": {
        "id": "101",
        "name": "Smoke Test",
        "description": "Basic functionality tests"
      },
      "total_tests": 50,
      "passed": 45,
      "failed": 3,
      "blocked": 1,
      "unexecuted": 1,
      "execution_rate": 98.0,
      "pass_rate": 90.0
    }
  ]
}
```

### Get Detailed Execution Information
```python
# Get detailed test execution data
result = await call_tool("get_execution_details", {
    "project_id": "10001",
    "version_id": "10100",
    "cycle_id": "101"  # Optional
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "executions": [
    {
      "id": "exec123",
      "testCaseName": "User Login Test",
      "executionStatus": "PASS",
      "executedBy": "john.doe",
      "executedOn": "2024-12-07T09:30:00",
      "defects": []
    }
  ],
  "total_count": 50
}
```

### Generate Comprehensive Test Report
```python
# Generate a complete test report for a release
result = await call_tool("generate_test_report", {
    "project_id": "10001",
    "version_id": "10100",
    "include_details": true  # Include detailed execution info
})
```

**Sample Output:**
```json
{
  "project_id": "10001",
  "version_id": "10100",
  "report_generated": "2024-12-07T10:45:00",
  "overall_metrics": {
    "total_tests": 450,
    "passed": 320,
    "failed": 45,
    "blocked": 15,
    "unexecuted": 70,
    "execution_rate": 84.4,
    "pass_rate": 71.1,
    "regression_test_count": 125,
    "negative_test_count": 35
  },
  "cycle_breakdown": [
    {
      "cycle": {
        "id": "101",
        "name": "Smoke Test"
      },
      "metrics": {
        "total": 50,
        "passed": 45,
        "failed": 3,
        "blocked": 1,
        "unexecuted": 1,
        "execution_rate": 98.0,
        "pass_rate": 90.0
      }
    }
  ],
  "defect_summary": {
    "totalDefects": 23,
    "openDefects": 8,
    "resolvedDefects": 15
  }
}
```

## Common Use Cases

### 1. Daily Standup Reporting
```python
# Get quick status for standup
progress = await call_tool("get_execution_progress", {
    "project_id": "10001",
    "version_id": "current_sprint"
})

defects = await call_tool("get_defect_summary", {
    "project_id": "10001",
    "version_id": "current_sprint"
})
```

### 2. Release Readiness Assessment
```python
# Comprehensive release status check
report = await call_tool("generate_test_report", {
    "project_id": "10001",
    "version_id": "v2.1.0",
    "include_details": false
})

# Check regression test coverage
regression = await call_tool("get_regression_test_count", {
    "project_id": "10001",
    "version_id": "v2.1.0"
})
```

### 3. Test Coverage Analysis
```python
# Analyze test coverage types
summary = await call_tool("get_test_execution_summary", {
    "project_id": "10001",
    "version_id": "v2.1.0"
})

negative_tests = await call_tool("get_negative_test_count", {
    "project_id": "10001",
    "version_id": "v2.1.0"
})
```

### 4. Quality Gate Checks
```python
# Check if quality gates are met
report = await call_tool("generate_test_report", {
    "project_id": "10001",
    "version_id": "v2.1.0"
})

# Quality criteria:
# - Execution rate > 95%
# - Pass rate > 90%
# - No critical defects open
# - All regression tests executed
```

## Integration Examples

### With CI/CD Pipeline
```bash
# In your pipeline script
python -c "
import asyncio
import json
from your_mcp_client import call_tool

async def check_release_quality():
    report = await call_tool('generate_test_report', {
        'project_id': '10001',
        'version_id': 'v2.1.0'
    })
    
    metrics = report['overall_metrics']
    if metrics['pass_rate'] < 90:
        print('FAIL: Pass rate below threshold')
        exit(1)
    
    print('PASS: Quality gates met')

asyncio.run(check_release_quality())
"
```

### With Slack/Teams Notifications
```python
# Send daily test status to Slack
async def send_daily_status():
    progress = await call_tool("get_execution_progress", {
        "project_id": "10001",
        "version_id": "current_sprint"
    })
    
    message = f"""
    📊 Daily Test Status:
    - Execution Rate: {progress['progress'][0]['execution_rate']:.1f}%
    - Pass Rate: {progress['progress'][0]['pass_rate']:.1f}%
    - Tests Remaining: {progress['progress'][0]['unexecuted']}
    """
    
    # Send to Slack/Teams
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify ZEPHYR_USERNAME/PASSWORD or ZEPHYR_ACCESS_KEY
   - Check if user has proper permissions

2. **Project Not Found**
   - Use `get_projects` to list available projects
   - Verify project ID format

3. **Version Not Found**
   - Check version ID in Zephyr UI
   - Some versions may be archived

4. **Empty Results**
   - Verify data exists in specified project/version
   - Check cycle and execution data in Zephyr

### Debug Mode
Set environment variable for detailed logging:
```bash
export ZEPHYR_MCP_DEBUG=1
```