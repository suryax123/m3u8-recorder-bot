import os
import asyncio
from typing import Optional
from config import RECORDING_PATH

class RecordingCancelled(Exception):
    pass

async def record_stream_async(
    url: str,
    duration_minutes: float,
    filename: str,
    cancel_event: Optional[asyncio.Event] = None
) -> Optional[str]:
    """
    Bulletproof M3U8 recording with aggressive retry/reconnect
    """
    os.makedirs(RECORDING_PATH, exist_ok=True)

    duration_sec = int(duration_minutes * 60)
    temp_file = os.path.join(RECORDING_PATH, f"{filename}_temp.mkv")
    final_file = os.path.join(RECORDING_PATH, f"{filename}.mp4")

    # Aggressive M3U8 handling flags
    record_cmd = [
        "ffmpeg", "-y",
        "-hide_banner",
        "-loglevel", "error",

        # HTTP/Network settings (CRITICAL for M3U8)
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",
        "-reconnect_at_eof", "1",
        "-multiple_requests", "1",
        "-http_persistent", "0",
        "-timeout", "30000000",  # 30 second timeout per segment

        # M3U8 specific settings
        "-seekable", "0",
        "-live_start_index", "-3",  # Start 3 segments back for stability

        # Protocol options
        "-protocol_whitelist", "file,http,https,tcp,tls,crypto",

        # Input with retries
        "-i", url,

        # Recording duration
        "-t", str(duration_sec),

        # Video mapping
        "-map", "0:v:0",
        "-map", "0:a?",

        # Video encoding (480p, low bandwidth)
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-maxrate", "800k",
        "-bufsize", "1600k",
        "-vf", "scale=-2:480",
        "-pix_fmt", "yuv420p",
        "-profile:v", "baseline",
        "-level", "3.0",

        # Audio encoding
        "-c:a", "aac",
        "-b:a", "96k",
        "-ac", "2",

        # Output to crash-safe MKV
        "-f", "matroska",
        temp_file
    ]

    process = None

    try:
        print(f"[{filename}] Starting M3U8 recording: {duration_minutes:.0f} min")
        print(f"[{filename}] URL: {url[:80]}...")

        process = await asyncio.create_subprocess_exec(
            *record_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        # Monitor process with cancellation check
        stderr_output = []
        while process.returncode is None:
            if cancel_event and cancel_event.is_set():
                raise RecordingCancelled()

            try:
                # Read stderr non-blocking
                if process.stderr:
                    try:
                        line = await asyncio.wait_for(process.stderr.readline(), timeout=1.0)
                        if line:
                            stderr_output.append(line.decode('utf-8', errors='ignore').strip())
                    except asyncio.TimeoutError:
                        pass

                # Wait for process with timeout
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                continue

        # Show errors if any
        if stderr_output:
            errors = [e for e in stderr_output if e and 'frame=' not in e.lower()]
            if errors:
                print(f"[{filename}] FFmpeg errors:")
                for err in errors[-10:]:  # Last 10 errors
                    print(f"  {err}")

        # Validate recording
        if not os.path.exists(temp_file):
            print(f"[{filename}] FAILED: No output file created")
            print(f"[{filename}] This usually means:")
            print(f"  - Stream URL is invalid or expired")
            print(f"  - Stream requires authentication")
            print(f"  - Network connectivity issue")
            return None

        file_size = os.path.getsize(temp_file)
        if file_size < 100_000:
            print(f"[{filename}] FAILED: File too small ({file_size} bytes)")
            print(f"[{filename}] Stream likely stopped immediately")
            os.remove(temp_file)
            return None

        print(f"[{filename}] Recorded {file_size / (1024*1024):.1f}MB")

        # Convert to MP4 for Telegram
        convert_cmd = [
            "ffmpeg", "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", temp_file,
            "-map", "0",
            "-c", "copy",
            "-movflags", "+faststart",
            "-f", "mp4",
            final_file
        ]

        print(f"[{filename}] Converting to MP4...")

        convert_process = await asyncio.create_subprocess_exec(
            *convert_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            await asyncio.wait_for(convert_process.wait(), timeout=600)
        except asyncio.TimeoutError:
            print(f"[{filename}] Conversion timeout")
            convert_process.kill()
            await convert_process.wait()
            return None

        if not os.path.exists(final_file):
            print(f"[{filename}] Conversion failed")
            return None

        final_size = os.path.getsize(final_file)
        if final_size < 100_000:
            print(f"[{filename}] Converted file too small")
            os.remove(final_file)
            return None

        print(f"[{filename}] Success! Final: {final_size / (1024*1024):.1f}MB")

        # Cleanup temp
        try:
            os.remove(temp_file)
        except:
            pass

        return final_file

    except RecordingCancelled:
        print(f"[{filename}] Cancelled")
        if process and process.returncode is None:
            process.kill()
            await process.wait()

        for f in [temp_file, final_file]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        raise

    except Exception as e:
        print(f"[{filename}] Exception: {e}")

        if process and process.returncode is None:
            try:
                process.kill()
                await process.wait()
            except:
                pass

        return None

def cleanup_file(filepath: str) -> bool:
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            return True
    except:
        pass
    return False

def get_file_size_mb(filepath: str) -> float:
    try:
        if os.path.exists(filepath):
            return os.path.getsize(filepath) / (1024 * 1024)
    except:
        pass
    return 0.0
