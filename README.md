# Agentic Smart Home Assistant

An extension of my **Voice-controlled Smart Home Assistant** project that adds an LLM-based agent for natural-language device control.

## What makes it agentic?

Instead of matching a fixed list of voice commands, the LLM decides which available tool should be used, passes structured arguments to that tool, receives the verified result, and then produces the final response.

**Flow:**

`User request → LLM agent → tool selection → device/sensor tool → verified result → LLM response`

## Tools

- `list_devices` – discovers registered devices
- `control_device` – turns devices on/off, changes fan speed, or sets AC temperature
- `get_device_status` – reads verified device state
- `get_temperature` – reads a simulated temperature sensor

The current version uses a JSON state file so the agent can be tested without hardware. The same tool functions can later be connected to ESP32/relay/IoT code.

## Example commands

- `Turn on the living room light.`
- `Is the bedroom fan on?`
- `Set the bedroom fan to speed 3.`
- `What's the temperature?`
- `Turn off the bedroom light.`

## Setup

1. Install Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and add your OpenAI API key.
4. Run the text agent:

```bash
python agent/smart_home_agent.py
```

Optional voice mode (requires a working microphone/PyAudio setup):

```bash
python voice_assistant.py
```

## Hardware integration

The repository already contains the original KiCad PCB/schematic files. For a physical prototype, replace the state-changing logic inside `control_device()` with the project's ESP32/relay communication layer (for example, serial, MQTT, or HTTP).

## Safety / reliability design

The agent can only call explicitly registered tools. It reads device state from the tool layer instead of inventing state, and ambiguous device requests are handled by device discovery/clarification.
