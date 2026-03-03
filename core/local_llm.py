"""
Local LLM Client - Uses OpenAI-compatible API to connect to local models
(Ollama, LM Studio, vLLM, etc. running in Docker or locally)
"""

from openai import OpenAI
from dataclasses import dataclass
from typing import Optional, List, Any


@dataclass
class ContentBlock:
    """Mimics Anthropic's content block structure"""
    type: str
    text: str = ""


@dataclass
class LocalMessage:
    """Mimics Anthropic's Message structure for compatibility"""
    content: List[ContentBlock]
    role: str
    model: str
    stop_reason: Optional[str] = None
    
    @property
    def text(self) -> str:
        """Get the text content from the message"""
        return "\n".join(
            block.text for block in self.content if block.type == "text"
        )


class LocalLLM:
    """
    Local LLM client that uses OpenAI-compatible API.
    Compatible with Ollama, LM Studio, vLLM, and other local LLM servers.
    """
    
    def __init__(self, model: str, base_url: str, api_key: str = "not-needed"):
        """
        Initialize the Local LLM client.
        
        Args:
            model: The model name (e.g., "llama3", "mistral", "codellama")
            base_url: The base URL of your local LLM server (e.g., "http://localhost:12434/v1")
            api_key: API key (usually "not-needed" for local servers)
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        self.base_url = base_url

    def add_user_message(self, messages: list, message):
        """Add a user message to the conversation history"""
        content = (
            message.text if isinstance(message, LocalMessage)
            else message.content if hasattr(message, 'content') and isinstance(message.content, str)
            else self._extract_text(message) if hasattr(message, 'content')
            else message
        )
        user_message = {"role": "user", "content": content}
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        """Add an assistant message to the conversation history"""
        content = (
            message.text if isinstance(message, LocalMessage)
            else message.content if hasattr(message, 'content') and isinstance(message.content, str)
            else self._extract_text(message) if hasattr(message, 'content')
            else message
        )
        assistant_message = {"role": "assistant", "content": content}
        messages.append(assistant_message)

    def _extract_text(self, message) -> str:
        """Extract text from message content blocks"""
        if hasattr(message, 'content'):
            if isinstance(message.content, list):
                return "\n".join(
                    block.text for block in message.content 
                    if hasattr(block, 'type') and block.type == "text"
                )
            return str(message.content)
        return str(message)

    def text_from_message(self, message: LocalMessage) -> str:
        """Extract text content from a message"""
        return "\n".join(
            block.text for block in message.content if block.type == "text"
        )

    def _convert_tools_for_openai(self, tools: List[dict]) -> List[dict]:
        """
        Convert Anthropic-style tools to OpenAI function calling format.
        """
        if not tools:
            return []
        
        openai_tools = []
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)
        return openai_tools

    def chat(
        self,
        messages: list,
        system: Optional[str] = None,
        temperature: float = 1.0,
        stop_sequences: List[str] = None,
        tools: Optional[List[dict]] = None,
        thinking: bool = False,
        thinking_budget: int = 1024,
    ) -> LocalMessage:
        """
        Send a chat request to the local LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system: System prompt
            temperature: Sampling temperature
            stop_sequences: List of stop sequences
            tools: List of tools (will be converted to OpenAI function format)
            thinking: Not supported by most local LLMs, ignored
            thinking_budget: Not supported by most local LLMs, ignored
            
        Returns:
            LocalMessage object compatible with the rest of the application
        """
        # Build the messages list with system prompt
        api_messages = []
        
        if system:
            api_messages.append({"role": "system", "content": system})
        
        # Add conversation messages
        for msg in messages:
            api_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Build request parameters
        params = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": 4096,  # Reasonable default for local models
        }

        if stop_sequences:
            params["stop"] = stop_sequences

        # Add tools if provided
        if tools:
            openai_tools = self._convert_tools_for_openai(tools)
            if openai_tools:
                params["tools"] = openai_tools
                params["tool_choice"] = "auto"

        # Make the API call
        try:
            response = self.client.chat.completions.create(**params)
            
            # Extract the response
            choice = response.choices[0]
            content_text = choice.message.content or ""
            
            # Handle tool calls if present
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                # Format tool calls as text for compatibility
                tool_info = []
                for tc in choice.message.tool_calls:
                    tool_info.append(f"Tool call: {tc.function.name}({tc.function.arguments})")
                if tool_info:
                    content_text += "\n" + "\n".join(tool_info)
            
            # Create response in Anthropic-compatible format
            return LocalMessage(
                content=[ContentBlock(type="text", text=content_text)],
                role="assistant",
                model=self.model,
                stop_reason=choice.finish_reason,
            )
            
        except Exception as e:
            # Return error as a message for debugging
            error_text = f"Error connecting to local LLM at {self.base_url}: {str(e)}"
            return LocalMessage(
                content=[ContentBlock(type="text", text=error_text)],
                role="assistant",
                model=self.model,
                stop_reason="error",
            )
