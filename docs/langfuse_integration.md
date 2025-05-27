# Langfuse Integration

This document explains how to set up and use Langfuse for monitoring and analyzing the code review agent's behavior.

## Overview

Langfuse is integrated into the code review agent to provide detailed monitoring, tracing, and analytics for the code review process. This includes tracking LLM calls, tool usage, and error rates.

## Features

- **Tracing**: Full trace of each code review request
- **LLM Monitoring**: Detailed tracking of all LLM interactions
- **Tool Usage**: Monitoring of all tool calls and their performance
- **Error Tracking**: Centralized error tracking and debugging
- **Performance Metrics**: Latency and success rates for all operations

## Setup

1. **Create a Langfuse Account**
   - Sign up at [Langfuse](https://cloud.langfuse.com)
   - Create a new project
   - Navigate to Project Settings > API Keys
   - Create a new public and secret key pair

2. **Configure Environment Variables**
   Add the following to your `.env` file:
   ```
   # Langfuse Configuration
   LANGFUSE_PUBLIC_KEY=your_public_key_here
   LANGFUSE_SECRET_KEY=your_secret_key_here
   # Optional: Uncomment and set if using a self-hosted Langfuse instance
   # LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. **Install Dependencies**
   Make sure you have the required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Once configured, Langfuse will automatically track:

- All LLM calls with inputs, outputs, and metadata
- Tool usage and performance metrics
- Errors and exceptions
- Custom events and metrics

### Viewing Traces

1. Log in to your Langfuse dashboard
2. Navigate to the "Traces" section
3. Filter by:
   - Trace ID
   - User ID
   - Status (success/error)
   - Date range
   - Custom metadata

### Key Metrics

- **Latency**: Time taken for each operation
- **Success Rate**: Percentage of successful operations
- **Token Usage**: Number of input/output tokens used
- **Error Rate**: Frequency of errors

## Advanced Configuration

### Custom Metadata

You can add custom metadata to traces by modifying the `metadata` parameter in the `@track_tool` decorator:

```python
@track_tool(
    name="custom_tool",
    metadata={
        "component": "custom_component",
        "team": "backend",
        "version": "1.0.0"
    }
)
async def my_tool():
    # Tool implementation
    pass
```

### Filtering Sensitive Data

By default, sensitive information like API keys are automatically redacted. You can customize this behavior in the Langfuse dashboard under Project Settings > Data Privacy.

## Troubleshooting

### Missing Traces

1. Verify your API keys are correct
2. Check your internet connection
3. Ensure the Langfuse client is properly initialized
4. Check the application logs for any error messages

### High Latency

If you notice increased latency, consider:

1. Batching multiple events together
2. Reducing the amount of data being sent
3. Using the async client for non-blocking operations

## Best Practices

1. **Tag Your Traces**: Use meaningful names and metadata
2. **Monitor Key Metrics**: Set up alerts for error rates and latency
3. **Regularly Review Logs**: Check for any unexpected behavior
4. **Update Regularly**: Keep the Langfuse SDK up to date

## Support

For issues with the Langfuse integration, please:

1. Check the [Langfuse Documentation](https://langfuse.com/docs)
2. Search the [GitHub Issues](https://github.com/your-repo/issues)
3. Open a new issue if your problem isn't already reported
