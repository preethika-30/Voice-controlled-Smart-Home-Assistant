import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

STATE_FILE = Path(__file__).resolve().parent / "device_state.json"

DEFAULT_STATE = {
    "living_room_light": {"type": "light", "room": "living room", "state": "off"},
    "bedroom_light": {"type": "light", "room": "bedroom", "state": "off"},
    "living_room_fan": {"type": "fan", "room": "living room", "state": "off", "speed": 0},
    "bedroom_fan": {"type": "fan", "room": "bedroom", "state": "off", "speed": 0},
    "air_conditioner": {"type": "ac", "room": "bedroom", "state": "off", "temperature": 24},
}


def load_state():
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps(DEFAULT_STATE, indent=2))
    return json.loads(STATE_FILE.read_text())


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def control_device(device: str, action: str, value: int | None = None) -> str:
    """Control one of the registered smart-home devices."""
    state = load_state()
    if device not in state:
        return f"Device '{device}' is not registered."

    item = state[device]
    action = action.lower()

    if action in {"on", "off"}:
        item["state"] = action
        if item["type"] == "fan" and action == "off":
            item["speed"] = 0
        save_state(state)
        return f"{device} is now {action}."

    if action == "speed":
        if item["type"] != "fan":
            return f"{device} does not support fan speed."
        if value is None or not 1 <= value <= 5:
            return "Fan speed must be between 1 and 5."
        item["state"] = "on"
        item["speed"] = value
        save_state(state)
        return f"{device} speed is now {value}."

    if action == "temperature":
        if item["type"] != "ac":
            return f"{device} does not support temperature control."
        if value is None or not 16 <= value <= 30:
            return "AC temperature must be between 16 and 30 C."
        item["temperature"] = value
        item["state"] = "on"
        save_state(state)
        return f"{device} is set to {value} C."

    return f"Unsupported action '{action}'."


def get_device_status(device: str) -> str:
    """Read the verified state of one registered device."""
    state = load_state()
    if device not in state:
        return f"Device '{device}' is not registered."
    return json.dumps({device: state[device]})


def list_devices() -> str:
    """List devices the agent is allowed to control."""
    state = load_state()
    return json.dumps({
        name: {"type": data["type"], "room": data["room"]}
        for name, data in state.items()
    })


def get_temperature() -> str:
    """Return a simulated indoor temperature sensor reading."""
    return "27 C (simulated sensor reading)"


TOOLS = [
    {
        "type": "function",
        "name": "control_device",
        "description": "Control a registered smart-home device. Use only devices returned by list_devices.",
        "parameters": {
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "Registered device name"},
                "action": {
                    "type": "string",
                    "enum": ["on", "off", "speed", "temperature"],
                },
                "value": {"type": ["integer", "null"], "description": "Speed 1-5 or AC temperature in Celsius"},
            },
            "required": ["device", "action", "value"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_device_status",
        "description": "Read the current verified state of a registered device.",
        "parameters": {
            "type": "object",
            "properties": {"device": {"type": "string"}},
            "required": ["device"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_devices",
        "description": "List all registered smart-home devices and their rooms.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function",
        "name": "get_temperature",
        "description": "Read the indoor temperature sensor.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

FUNCTIONS = {
    "control_device": control_device,
    "get_device_status": get_device_status,
    "list_devices": list_devices,
    "get_temperature": get_temperature,
}

INSTRUCTIONS = """You are a smart-home agent. Help the user control and monitor registered devices.

Rules:
1. Use tools for device actions and sensor readings; never invent device state.
2. If you do not know a device name, call list_devices before controlling anything.
3. Do not claim an action succeeded until the control_device tool returns success.
4. For ambiguous commands such as 'turn on the light', use list_devices and ask for clarification if multiple devices could match.
5. Keep responses short and friendly.
6. You may interpret natural language such as 'make the bedroom cooler' as setting the bedroom AC to a reasonable temperature, but ask if the intended temperature is unclear.
"""


def run_agent(user_text: str) -> str:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-5.5"),
        instructions=INSTRUCTIONS,
        input=user_text,
        tools=TOOLS,
    )

    # Agent loop: execute every requested tool, then give results back to the model.
    while True:
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text

        outputs = []
        for call in calls:
            try:
                args = json.loads(call.arguments)
                result = FUNCTIONS[call.name](**args)
            except Exception as exc:
                result = f"Tool error: {exc}"
            outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": str(result),
            })

        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-5.5"),
            instructions=INSTRUCTIONS,
            previous_response_id=response.id,
            input=outputs,
            tools=TOOLS,
        )


if __name__ == "__main__":
    print("Agentic Smart Home Assistant")
    print("Type 'exit' to stop. Example: Turn on the living room light.\n")
    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit"}:
            break
        try:
            print("Assistant:", run_agent(user_text))
        except Exception as exc:
            print("Error:", exc)
