"""Tool schemas for OpenRouter function calling."""

READ_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative path to the file within the project",
        }
    },
    "required": ["path"],
    "additionalProperties": False,
}

WRITE_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative path to the file within the project",
        },
        "content": {
            "type": "string",
            "description": "UTF-8 text content to write to the file",
        },
    },
    "required": ["path", "content"],
    "additionalProperties": False,
}

LIST_FILES_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative directory path within the project",
            "default": ".",
        },
        "recursive": {
            "type": "boolean",
            "description": "Whether to list files recursively",
            "default": True,
        },
    },
    "additionalProperties": False,
}

SEARCH_FILES_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Text to search for in project files",
        },
        "path": {
            "type": "string",
            "description": "Relative directory path to search in",
            "default": ".",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "minimum": 1,
            "maximum": 100,
            "default": 50,
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

RUN_COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The command to execute.",
        },
        "timeout": {
            "type": "integer",
            "description": "Maximum execution time in seconds.",
            "minimum": 1,
            "maximum": 300,
            "default": 30,
        },
    },
    "required": ["command"],
    "additionalProperties": False,
}

WEB_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query.",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results.",
            "minimum": 1,
            "maximum": 10,
            "default": 5,
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}


def get_tool_definitions() -> list[dict]:
    """Return all tool definitions for the AI model."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a UTF-8 text file inside the project.",
                "parameters": READ_FILE_SCHEMA,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create or replace a UTF-8 text file inside the project.",
                "parameters": WRITE_FILE_SCHEMA,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files and directories inside the project.",
                "parameters": LIST_FILES_SCHEMA,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Search text inside UTF-8 project files.",
                "parameters": SEARCH_FILES_SCHEMA,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Run an approved local development command inside the selected project directory.",
                "parameters": RUN_COMMAND_SCHEMA,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the internet for relevant information and return search results with titles, URLs, and snippets.",
                "parameters": WEB_SEARCH_SCHEMA,
            },
        },
    ]
