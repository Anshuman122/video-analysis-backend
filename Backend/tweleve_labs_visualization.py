import os
import json
import uuid
import httpx
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem


def analyze_video(video_url_or_path: str, api_key: str = None, output_file: str = None) -> dict:
    """
    Analyze a video using Twelve Labs.
    Supports both local files and remote URLs.
    Returns dict with 'scenes' (list of {"start_time", "end_time", "visual"}).
    """

    api_key = api_key or os.getenv("twelve_labs_apis")
    if not api_key:
        raise ValueError("Twelve Labs API key not found. Set `twelve_labs_apis` env variable.")

    client = TwelveLabs(api_key=api_key, httpx_client=httpx.Client(timeout=600.0))

    # Create a unique index
    index_name = f"video_analysis_index_{uuid.uuid4().hex[:8]}"
    index = client.indexes.create(
        index_name=index_name,
        models=[IndexesCreateRequestModelsItem(model_name="pegasus1.2", model_options=["visual"])]
    )

    # Create task depending on file type
    if video_url_or_path.startswith("http"):
        task = client.tasks.create(index_id=index.id, video_url=video_url_or_path)
    else:
        task = client.tasks.create(index_id=index.id, file=video_url_or_path)

    # Wait for indexing to complete
    task = client.tasks.wait_for_done(task_id=task.id, callback=lambda t: print(f"  ⏳ Status={t.status}"))
    if task.status != "ready":
        raise RuntimeError(f"Indexing failed with status {task.status}")

    # Analyze video in a streaming fashion
    text_stream = client.analyze_stream(
        video_id=task.video_id,
        prompt="""
Analyze the entire video in 25-second intervals strictly.
Only provide detailed visual analysis for each segment.
Do not include audio.

Return JSON strictly as:
{
  "scenes": [
    {"start_time": <int>, "end_time": <int>, "visual": "<detailed visual description>"}
  ]
}
"""
    )

    # Accumulate all generated text
    raw_output = "".join(event.text for event in text_stream if event.event_type == "text_generation")

    # Attempt to parse JSON safely
    try:
        analysis_json = json.loads(raw_output)
    except json.JSONDecodeError:
        # Fallback: wrap raw_output as "raw_output" if parsing fails
        analysis_json = {"scenes": [], "raw_output": raw_output}

    # Ensure 'scenes' key exists
    if "scenes" not in analysis_json:
        analysis_json["scenes"] = []

    # Save to file if requested
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis_json, f, indent=2, ensure_ascii=False)

    return analysis_json
