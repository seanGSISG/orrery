"""ComfyUI API client and the two backing-track workflows.

The workflows are the API form of ComfyUI's own templates `audio_ace_step1_5_xl_turbo`
and `audio_stable_audio_3_medium`, with two changes: no optional Qwen reprompt step (our
prompts are already in the caption form that reprompt produces), and a core
AudioAdjustVolume node before saving (see HEADROOM_DB). Use `run_take`
to render one take; it blocks until ComfyUI finishes and returns the downloaded file.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

COMFY_URL = "http://127.0.0.1:8188"
# Both models decode hot masters that pass full scale, and SaveAudio's FLAC clamps them.
# 6 dB of headroom before saving keeps the peaks; loudness is normalised later anyway.
HEADROOM_DB = -6

Model = Literal["ace-step-1.5-xl-turbo", "stable-audio-3-medium"]

type Workflow = dict[str, dict[str, object]]


@dataclass(frozen=True)
class TakeRequest:
    """One backing-track render: the prompt, seed and settings sent to ComfyUI."""

    model: Model
    prompt: str
    seed: int
    seconds: float
    bpm: int
    key: str
    steps: int = 8
    shift: float = 3.0
    lm_cfg: float = 2.0
    lm_temperature: float = 0.85


def ace_step_workflow(req: TakeRequest, prefix: str) -> Workflow:
    """ACE-Step 1.5 XL turbo, instrumental: tags, BPM and key go to the 1.7B planner LM."""
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "acestep_v1.5_xl_turbo_bf16.safetensors",
                "weight_dtype": "default",
            },
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "qwen_0.6b_ace15.safetensors",
                "clip_name2": "qwen_1.7b_ace15.safetensors",
                "type": "ace",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "ace_1.5_vae.safetensors"},
        },
        "4": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["1", 0], "shift": req.shift},
        },
        "5": {
            "class_type": "TextEncodeAceStepAudio1.5",
            "inputs": {
                "clip": ["2", 0],
                "tags": req.prompt,
                "lyrics": "[Instrumental]",
                "seed": req.seed,
                "bpm": req.bpm,
                "duration": req.seconds,
                "timesignature": "4",
                "language": "en",
                "keyscale": req.key,
                "generate_audio_codes": True,
                "cfg_scale": req.lm_cfg,
                "temperature": req.lm_temperature,
                "top_p": 0.9,
                "top_k": 0,
                "min_p": 0.0,
            },
        },
        "6": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["5", 0]},
        },
        "7": {
            "class_type": "EmptyAceStep1.5LatentAudio",
            "inputs": {"seconds": req.seconds, "batch_size": 1},
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["7", 0],
                "seed": req.seed,
                "steps": req.steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "9": {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["8", 0], "vae": ["3", 0]},
        },
        "10": {
            "class_type": "AudioAdjustVolume",
            "inputs": {"audio": ["9", 0], "volume": HEADROOM_DB},
        },
        "11": {
            "class_type": "SaveAudio",
            "inputs": {"audio": ["10", 0], "filename_prefix": prefix},
        },
    }


def stable_audio_workflow(req: TakeRequest, prefix: str) -> Workflow:
    """Stable Audio 3 Medium: one caption (BPM and length written in the text), 8 LCM steps."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "stable_audio_3_medium.safetensors"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "t5gemma_b_b_ul2.safetensors",
                "type": "stable_audio",
                "device": "default",
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": req.prompt},
        },
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
        "5": {
            "class_type": "EmptyLatentAudio",
            "inputs": {"seconds": req.seconds, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": req.seed,
                "steps": req.steps,
                "cfg": 1.0,
                "sampler_name": "lcm",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "7": {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "AudioAdjustVolume",
            "inputs": {"audio": ["7", 0], "volume": HEADROOM_DB},
        },
        "9": {
            "class_type": "SaveAudio",
            "inputs": {"audio": ["8", 0], "filename_prefix": prefix},
        },
    }


def workflow(req: TakeRequest, prefix: str) -> Workflow:
    """The API workflow for the request's model."""
    return (
        ace_step_workflow(req, prefix)
        if req.model == "ace-step-1.5-xl-turbo"
        else stable_audio_workflow(req, prefix)
    )


class ComfyError(RuntimeError):
    """ComfyUI rejected the workflow or the run failed."""


def _get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def comfy_version() -> str:
    system = _get_json(f"{COMFY_URL}/system_stats")["system"]
    return str(system["comfyui_version"]) if isinstance(system, dict) else "unknown"


def run_take(req: TakeRequest, dest: Path, timeout_s: float = 900.0) -> Path:
    """Queue one take, wait for it, and save the FLAC to `dest`. ComfyUI runs one job at a time."""
    body = json.dumps(
        {"prompt": workflow(req, f"orrery/{dest.stem}"), "client_id": str(uuid.uuid4())}
    ).encode()
    post = urllib.request.Request(
        f"{COMFY_URL}/prompt", data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(post, timeout=30) as resp:
            prompt_id = str(json.load(resp)["prompt_id"])
    except urllib.error.HTTPError as err:
        raise ComfyError(err.read().decode(errors="replace")) from err
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        history = _get_json(f"{COMFY_URL}/history/{prompt_id}")
        entry = history.get(prompt_id)
        if isinstance(entry, dict):
            status = entry.get("status", {})
            if isinstance(status, dict) and status.get("status_str") == "error":
                raise ComfyError(json.dumps(status.get("messages"))[:2000])
            for output in entry.get("outputs", {}).values():
                for item in output.get("audio", []):
                    query = urllib.parse.urlencode(
                        {
                            "filename": item["filename"],
                            "subfolder": item["subfolder"],
                            "type": item["type"],
                        }
                    )
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with urllib.request.urlopen(
                        f"{COMFY_URL}/view?{query}", timeout=60
                    ) as resp:
                        dest.write_bytes(resp.read())
                    return dest
        time.sleep(2.0)
    raise ComfyError(f"timed out after {timeout_s:.0f} s waiting for {prompt_id}")
