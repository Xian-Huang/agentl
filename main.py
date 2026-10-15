import json
import os
import re
import httpx
from .tools import register_tools

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("MODEL", "deepseek-chat")


class LLMChannel:

    def __init__(self, api_key: str = deepseek_api_key, base_url: str = BASE_URL, model: str = MODEL):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def send_request(self, messages: list, tools: list = None, temperature: float = 0.7, max_tokens: int = 150):

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "temperature": temperature, "messages": messages, "tools": tools, "max_tokens": max_tokens}

        resp = httpx.post(url=f"{self.base_url}/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"Request failed with status code {resp.status_code}: {resp.text}")
        
        return resp.json()['choices'][0]['message']



class ReActAgent():

    def __init__(self):
        self.max_retry = 3
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.channel = LLMChannel()
        self.trace = []
    
    
    def send_messages(self, messages: list, tools: list = None, temperature: float = 0.7, max_tokens: int = 150):
        """
        Send a request to the LLM channel and return the response.
        """
        for attempt in range(self.max_retry):
            try:
                response = self.channel.send_request(messages=messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
                return response
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retry - 1:
                    raise
                
            
    def _execute_tool(self, tool_call):
        """
        Execute the tool call and return the result.
        """
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        trace = {"tool_call": tool_call, "function_name": function_name, "function_args": function_args}
        self.trace.append(trace)
        
        
        if function_name in register_tools:
            tool_result = register_tools[function_name](**function_args)
            trace["tool_result"] = tool_result
            return tool_result
        
    
    def chat(self, input, tools: list = None, temperature: float = 0.7, max_tokens: int = 150):
        """
        Chat with the ReAct agent using the provided messages and tools.
        """
        
        self.trace = []
        
        self.messages.append({"role": "user", "content": input})
        while True:
            response = self.send_messages(messages=self.messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
            self.messages.append(response)
            if not response.get("tool_calls"):
                return response
            for tool_call in response.get("tool_calls", []):
                tool_result = self._excecute_tool(tool_call)
                self.messages.append({"role": "tool", "content": tool_result})