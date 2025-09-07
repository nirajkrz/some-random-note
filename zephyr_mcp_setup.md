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