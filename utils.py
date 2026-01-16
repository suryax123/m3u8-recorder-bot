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
    M3U8 recording with proper duration control
    """
    os.makedirs(RECORDING_PATH, exist_ok=True)
    
    duration_sec = int(duration_minutes * 60)
    temp_file = os.path.join(RECORDING_PATH, f"{filename}_temp.mkv")
    final_file = os.path.join(RECORDING_PATH, f"{filename}.mp4")
    
    # M3U8 optimized settings WITHOUT infinite reconnect
    record_cmd = [
        "ffmpeg", "-y",
        "-hide_banner",
        "-loglevel", "error",
        
        # Network settings for M3U8
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-multiple_requests", "1",
        "-timeout", "15000000",  # 15 second timeout
        
        # Protocol whitelist
        "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
        
        # Input
        "-i", url,
        
        # CRITICAL: Duration BEFORE mapping to ensure it's respected
        "-t", str(duration_sec),
        
        # Mapping
        "-map", "0:v:0",
        "-map", "0:a?",
        
        # Video encoding
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
        
        # Output
        "-f", "matroska",
        temp_file
    ]
    
    process = None
    start_time = asyncio.get_event_loop().time()
    max_duration = duration_sec + 60  # Safety: max duration + 1 minute buffer
    
    try:
        print(f"[{filename}] Recording for {duration_minutes:.0f} minutes")
        
        process = await asyncio.create_subprocess_exec(
            *record_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Monitor with timeout enforcement
        while process.returncode is None:
            # Check cancellation
            if cancel_event and cancel_event.is_set():
                raise RecordingCancelled()
            
            # Check duration timeout (safety mechanism)
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_duration:
                print(f"[{filename}] TIMEOUT: Exceeded max duration ({max_duration}s), killing process")
                process.kill()
                break
            
            # Read stderr
            if process.stderr:
                try:
                    line = await asyncio.wait_for(process.stderr.readline(), timeout=1.0)
                    if line:
                        err = line.decode('utf-8', errors='ignore').strip()
                        if err and 'frame=' not in err.lower():
                            print(f"[{filename}] {err}")
                except asyncio.TimeoutError:
                    pass
            
            # Wait with short timeout
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                continue
        
        actual_duration = asyncio.get_event_loop().time() - start_time
        print(f"[{filename}] Process ended after {actual_duration:.0f} seconds (target: {duration_sec}s)")
        
        # Validate recording
        if not os.path.exists(temp_file):
            print(f"[{filename}] FAILED: No output file")
            return None
        
        file_size = os.path.getsize(temp_file)
        if file_size < 100_000:
            print(f"[{filename}] FAILED: File too small ({file_size} bytes)")
            os.remove(temp_file)
            return None
        
        print(f"[{filename}] Recorded {file_size / (1024*1024):.1f}MB")
        
        # Convert to MP4
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
        
        print(f"[{filename}] Success! {final_size / (1024*1024):.1f}MB")
        
        # Cleanup
        try:
            os.remove(temp_file)
        except:
            pass
        
        return final_file
        
    except RecordingCancelled:
        print(f"[{filename}] Cancelled by user")
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
