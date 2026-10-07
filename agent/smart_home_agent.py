import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI()

# Location of device state file
STATE_FILE = Path(__file__).parent / "device_state.json"


def load_devices():
    """Load the current smart-home device status."""
    with open(STATE_FILE, "r") as file:
        return json.load(file)


def save_devices(devices):
    """Save updated device status."""
    with open(STATE_FILE, "w") as file:
        json.dump(devices, file, indent=4)


def control_device(device, action):
    """Turn a smart-home device on or off."""
    devices = load_devices()

    if device not in devices:
        return f"Device '{device}' was not found."

    if action not in ["on", "off"]:
        return "Action must be 'on' or 'off'."

    devices[device]["status"] = action
    save_devices(devices)

    return f"{device} has been turned {action}."


def get_device_status(device):
    """Check the status of a device."""
    devices = load_devices()

    if device not in devices:
        return f"Device '{device}' was not found."

    return f"{device} is currently {devices[device]['status']}."


def list_devices():
    """List all available smart-home devices."""
    devices = load_devices()

    return ", ".join(devices.keys())


tools = [
    {
        "type": "function",
        "function": {
            "name": "control_device",
            "description": "Turn a smart-home device on or off.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "description": "Name of the smart-home device"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "Action to perform"
                    }
                },
                "required": ["device", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_status",
            "description": "Check the current status of a smart-home device.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "description": "Name of the smart-home device"
                    }
                },
                "required": ["device"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_devices",
            "description": "List all available smart-home devices.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def run_agent(user_request):
    """Let the AI decide which smart-home tool should be used."""

    response = client.chat.completions.create(
        model="YOUR_API_MODEL",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a smart home assistant. "
                    "Understand the user's request and use the available "
                    "tools when a device action or status check is required."
                )
            },
            {
                "role": "user",
                "content": user_request
            }
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if not message.tool_calls:
        return message.content

    results = []

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "control_device":
            result = control_device(
                arguments["device"],
                arguments["action"]
            )

        elif function_name == "get_device_status":
            result = get_device_status(
                arguments["device"]
            )

        elif function_name == "list_devices":
            result = list_devices()

        else:
            result = "Unknown tool."

        results.append(result)

    return "\n".join(results)


if __name__ == "__main__":
    print("Smart Home Agent")
    print("----------------")
    print("Example: Turn on the living room light")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        answer = run_agent(user_input)
        print("Assistant:", answer)
