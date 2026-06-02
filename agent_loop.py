import json
import requests
from typing import Callable, Dict, List

OPENAI_API_KEY = "sk-your-api-key-here"
MODEL = "gpt-4o-mini"
API_URL = "https://api.openai.com/v1/chat/completions"

TOOL_REGISTRY: Dict[str, dict] = {}

def tool(name, description, parameters):
    def decorator(func):
        TOOL_REGISTRY[name] = {"function": func, "schema": {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}}
        return func
    return decorator

@tool("get_weather","Get weather for a location",{"type":"object","properties":{"location":{"type":"string","description":"City name"}},"required":["location"]})
def get_weather(location):
    data={"new york":"72F Partly cloudy","london":"59F Rainy","paris":"68F Sunny","tokyo":"81F Humid"}
    return data.get(location.lower(),f"No data for {location}")

@tool("calculate","Evaluate a math expression",{"type":"object","properties":{"expression":{"type":"string","description":"Math expression"}},"required":["expression"]})
def calculate(expression):
    try:
        return f"Result: {eval(expression,{chr(39)}__builtins__{chr(39)}: {}}, {})}"
    except Exception as e:
        return f"Error: {e}"

@tool("search_notes","Search saved notes",{"type":"object","properties":{"query":{"type":"string","description":"Search query"}},"required":["query"]})
def search_notes(query):
    notes=["Meeting at 3pm with design team","Buy groceries milk eggs bread","Project deadline Friday December 20th","Call dentist to schedule appointment"]
    results=[n for n in notes if query.lower() in n.lower()]
    return chr(10).join(results) if results else "No matching notes found."

class AgentLoop:
    def __init__(self,system_prompt="You are a helpful assistant."):
        self.system_prompt=system_prompt
        self.history=[]
        self.max_rounds=10

    def get_tool_schemas(self):
        return [t["schema"] for t in TOOL_REGISTRY.values()]

    def call_llm(self,messages):
        headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"}
        payload={"model":MODEL,"messages":messages,"tools":self.get_tool_schemas(),"tool_choice":"auto"}
        resp=requests.post(API_URL,headers=headers,json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]

    def execute_tool(self,tool_call):
        name=tool_call["function"]["name"]
        args=json.loads(tool_call["function"]["arguments"])
        print(f"    Tool: {name}({args})")
        if name in TOOL_REGISTRY:
            result=TOOL_REGISTRY[name]["function"](**args)
            print(f"    Result: {result}")
            return result
        return f"Error: Unknown tool {name}"

    def run(self,user_message):
        print(f"\n{"="*50}")
        print(f"Step 1: Received message")
        print(f"   {user_message}")
        self.history.append({"role":"user","content":user_message})
        messages=[{"role":"system","content":self.system_prompt}]
        messages.extend(self.history)
        rounds=0
        while rounds<self.max_rounds:
            rounds+=1
            print(f"\nSteps 2-3: Agent thinking (round {rounds})...")
            assistant_msg=self.call_llm(messages)
            messages.append(assistant_msg)
            if assistant_msg.get("tool_calls"):
                n=len(assistant_msg["tool_calls"])
                print(f"Step 4: {n} tool call(s)")
                for tc in assistant_msg["tool_calls"]:
                    result=self.execute_tool(tc)
                    print(f"Step 5: Feeding result back")
                    messages.append({"role":"tool","tool_call_id":tc["id"],"content":result})
            else:
                print(f"\nStep 6: Final response produced")
                final=assistant_msg["content"]
                self.history.append({"role":"assistant","content":final})
                print(f"Step 7: Sending response back")
                print(f"{"="*50}\n")
                return final
        return "Error: Max tool rounds exceeded."

def main():
    print("Agent Loop Chat")
    print("Type quit to exit / clear to reset")

    agent=AgentLoop(system_prompt="You are a helpful assistant with tools. Use them when needed.")

    while True:
        user_input=input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower()=="quit":
            print("Goodbye!")
            break
        if user_input.lower()=="clear":
            agent.history.clear()
            print("Conversation cleared.")
            continue
        response=agent.run(user_input)
        print(f"Agent: {response}")

if __name__=="__main__":
    main()
