import os
import re
import json
import uuid
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse

from .transcription import convert_drive_link

def analyze_video(video_source: str, api_key: str = None) -> dict:
    api_key = api_key or os.getenv("twelve_labs_apis")
    if not api_key:
        raise ValueError("Set the TWELVE_LABS_API_KEY environment variable")

    if video_source.startswith("http") and "drive.google.com" in video_source:
        video_source = convert_drive_link(video_source)
        print(f"🔗 Converted Google Drive link for Twelve Labs: {video_source}")

    client = TwelveLabs(api_key=api_key, timeout=600)

    index_name = f"video-analysis-{uuid.uuid4().hex[:8]}"
    print(f"⏳ Creating Twelve Labs index '{index_name}'...")
    index = client.indexes.create(
        index_name=index_name,
        models=[
            IndexesCreateRequestModelsItem(
                model_name="pegasus1.2",
                model_options=["visual"]
            )
        ]
    )
    print(f"✅ Twelve Labs index '{index.id}' created.")


    task = client.tasks.create(index_id=index.id, video_url=video_source)
    print(f"⏳ Indexing video with task ID: {task.id}")


    def on_task_update(task: TasksRetrieveResponse):
        print(f"  Task status: {task.status}")

    task = client.tasks.wait_for_done(task_id=task.id, callback=on_task_update)

    if task.status != "ready":
        raise RuntimeError(f"Task failed with status {task.status}")
    print(f"✅ Task completed. Video ID: {task.video_id}")

    print(f"🧠 Generating visual analysis for video {task.video_id}...")
    text_stream = client.analyze_stream(video_id=task.video_id, prompt="""
    Analyze the entire video in 25-second intervals strictly.
    Only provide detailed visual analysis for each segment.
    Do not include audio.

    Return JSON strictly as:
    {
      "scenes": [
        {"start_time": <int>, "end_time": <int>, "visual": "<detailed visual description>"}
      ]
    }
    """)
    
    raw_output = "".join(text.text for text in text_stream if text.event_type == "text_generation")

    client.indexes.delete(index.id)
    print(f"✅ Deleted Twelve Labs index '{index.id}'")
    visual_output_path = os.path.join("reports", "visual_analysis.json")
    os.makedirs(os.path.dirname(visual_output_path), exist_ok=True)
    with open(visual_output_path, "w", encoding="utf-8") as f:
        f.write(raw_output)
    print(f"💾 Raw visual analysis output saved to {visual_output_path}")
    
    try:

        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
            json_string = re.sub(r',\s*([\}\]])', r'\1', json_string)
            analysis_json = json.loads(json_string)
            print("✅ Successfully extracted and parsed generated JSON.")
            return analysis_json
        else:
          
            raise json.JSONDecodeError("No JSON object found in the output.", raw_output, 0)
            
    except json.JSONDecodeError as e:
        print(f"❌ Error: Failed to parse JSON from the generative output. Reason: {e}")
        return {"scenes": [], "error": "Failed to parse JSON", "raw_output": raw_output}
    
    
