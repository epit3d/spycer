"""
GRPC client for remote slicer service.
Uses job-based asynchronous API.
"""
import logging
import grpc
import time
import zipfile
import io
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

import src.server_api.pyapi.srv_slicer.srv_slicer_pb2 as srv_slicer_pb2
import src.server_api.pyapi.srv_slicer.srv_slicer_pb2_grpc as srv_slicer_pb2_grpc
from src.settings import sett

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1MB


class SlicerClient:
    """Client for remote slicer GRPC service using job-based async API."""
    
    @staticmethod
    def get_server_address() -> str:
        """Get the remote slicer server address from settings."""
        s = sett()
        # Try to get from settings, fallback to default
        if hasattr(s, 'remote_slicer_address'):
            return s.remote_slicer_address
        return "localhost:50051"  # Default address
    
    @staticmethod
    def check_connection(address: Optional[str] = None, timeout: int = 5) -> bool:
        """
        Check if the remote slicer server is reachable.
        
        Args:
            address: Server address (host:port). If None, uses settings.
            timeout: Connection timeout in seconds.
            
        Returns:
            True if server is reachable, False otherwise.
        """
        if address is None:
            address = SlicerClient.get_server_address()
            
        try:
            logger.info(f"Checking connection to remote slicer at {address}")
            with grpc.insecure_channel(address) as channel:
                grpc.channel_ready_future(channel).result(timeout=timeout)
            logger.info("Connection successful")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to remote slicer: {e}")
            return False
    
    @staticmethod
    def _create_archive(stl_file: Path, settings_yaml: str) -> bytes:
        """
        Create a zip archive containing the STL file, settings, and required data files.
        
        Args:
            stl_file: Path to the STL file.
            settings_yaml: Settings in YAML format.
            
        Returns:
            Zip archive as bytes.
        """
        from src.settings import APP_PATH
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add settings with expected name
            zipf.writestr('sett_example.yaml', settings_yaml)
            
            # Add STL file at root of archive (simple path)
            zipf.write(stl_file, arcname=stl_file.name)
            
            # Add required data files (calibration data and templates)
            # Get printer directory from settings if available
            settings_obj = sett()
            printer_dir = None
            if settings_obj and hasattr(settings_obj, 'hardware'):
                printer_dir = getattr(settings_obj.hardware, 'printer_dir', None)
            
            # Map data files to archive
            data_files = {}
            
            # Add calibration from printer directory if available
            if printer_dir and Path(printer_dir).exists():
                printer_path = Path(printer_dir)
                calib_file = printer_path / 'calibration_data.csv'
                if calib_file.exists():
                    data_files['data/calibration_data.csv'] = calib_file
            
            # Fallback to default calibration files
            if 'data/calibration_data.csv' not in data_files:
                data_files['data/calibration_data.csv'] = APP_PATH / 'data/calibration_data.csv'
            
            data_files.update({
                'data/calibration_data_zero.csv': APP_PATH / 'data/calibration_data_zero.csv',
                'data/header_template.txt': APP_PATH / 'data/header_template.txt',
                'data/footer_template.txt': APP_PATH / 'data/footer_template.txt',
            })
            
            for archive_path, file_path in data_files.items():
                if file_path.exists():
                    zipf.write(file_path, arcname=archive_path)
                else:
                    logger.warning(f"Data file not found: {file_path}")
        
        return buffer.getvalue()
    
    @staticmethod
    def _generate_submit_job_chunks(archive_data: bytes, archive_filename: str):
        """
        Generate chunks for streaming upload.
        
        Args:
            archive_data: Complete archive as bytes.
            archive_filename: Name of the archive file.
            
        Yields:
            SubmitJobRequest messages with config and chunks.
        """
        # First message: job configuration
        config = srv_slicer_pb2.JobConfig(
            job_name="slice_stl",
            settings_relative_path="sett_example.yaml",  # Must match filename in archive
            archive_filename=archive_filename,
        )
        yield srv_slicer_pb2.SubmitJobRequest(config=config)
        
        # Subsequent messages: file chunks
        for i in range(0, len(archive_data), CHUNK_SIZE):
            chunk_data = archive_data[i:i + CHUNK_SIZE]
            file_chunk = srv_slicer_pb2.FileChunk(data=chunk_data)
            yield srv_slicer_pb2.SubmitJobRequest(chunk=file_chunk)
    
    @staticmethod
    def slice_stl(
        stl_file: Path,
        output_dir: Path,
        address: Optional[str] = None,
        timeout: int = 300,
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        Slice an STL file using the remote slicer service (job-based async API).
        
        Args:
            stl_file: Path to the input STL file.
            output_dir: Directory where output files should be saved.
            address: Server address (host:port). If None, uses settings.
            timeout: Maximum time to wait for job completion in seconds.
            poll_interval: Time between status polls in seconds.
            
        Returns:
            Dict with status and file paths:
            {
                "success": bool,
                "job_id": str or None,
                "gcode_file": Path or None,
                "gcodevis_file": Path or None,
                "error": str or None
            }
        """
        if address is None:
            address = SlicerClient.get_server_address()
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Slicing {stl_file} via remote slicer at {address}")
            
            # Get settings as YAML string
            settings_obj = sett()
            if settings_obj is None:
                raise ValueError(
                    "Settings not loaded. Call load_settings() first or ensure settings.yaml exists."
                )
            settings_dict = settings_obj.to_dict()  # type: ignore[attr-defined]
            
            # Remove/update paths that would be absolute on the server
            # The server will extract the archive to its workspace, so all paths must be relative
            if 'project_path' in settings_dict:
                # Remove or set to current directory
                settings_dict['project_path'] = '.'  # type: ignore[index]
            
            # Update hardware paths to point to data files in archive
            if 'hardware' in settings_dict and isinstance(settings_dict['hardware'], dict):  # type: ignore[index]
                # Point to calibration data included in archive
                settings_dict['hardware']['printer_dir'] = 'data'  # type: ignore[index]
                # calibration_file stays as-is (just filename)
            
            # Update STL file paths to match archive structure (just filename at root)
            if 'slicing' in settings_dict and isinstance(settings_dict['slicing'], dict):  # type: ignore[index]
                # Use just the filename since STL is at root of archive
                settings_dict['slicing']['stl_file'] = stl_file.name  # type: ignore[index]
                settings_dict['slicing']['stl_filename'] = stl_file.name  # type: ignore[index]
                # Also update copy_stl_file if it exists
                if 'copy_stl_file' in settings_dict['slicing']:  # type: ignore[index]
                    settings_dict['slicing']['copy_stl_file'] = stl_file.name  # type: ignore[index]
            
            logger.debug(f"STL path in settings: {settings_dict.get('slicing', {}).get('stl_file', 'N/A')}")  # type: ignore[union-attr]
            settings_yaml = yaml.dump(settings_dict)
            
            # Create archive
            logger.info("Creating archive...")
            archive_data = SlicerClient._create_archive(stl_file, settings_yaml)
            
            # Open a channel
            with grpc.insecure_channel(address) as channel:
                stub = srv_slicer_pb2_grpc.SlicerServiceStub(channel)
                
                # Submit job
                logger.info(f"Submitting job (archive size: {len(archive_data)} bytes)...")
                # Try using a simple archive name
                archive_filename = "archive.zip"
                logger.debug(f"Archive filename: {archive_filename}")
                logger.debug("Settings path in config: settings.yaml")
                chunk_stream = SlicerClient._generate_submit_job_chunks(archive_data, archive_filename)
                job_response = stub.SubmitJob(chunk_stream, timeout=30)
                
                job_id = job_response.job_id
                logger.info(f"Job submitted: {job_id}")
                
                # Poll for job completion
                start_time = time.time()
                while True:
                    if time.time() - start_time > timeout:
                        return {
                            "success": False,
                            "job_id": job_id,
                            "gcode_file": None,
                            "gcodevis_file": None,
                            "error": f"Timeout waiting for job {job_id}"
                        }
                    
                    # Get job status
                    status_request = srv_slicer_pb2.GetJobRequest(job_id=job_id)
                    job_status = stub.GetJob(status_request, timeout=10)
                    
                    state = job_status.state
                    logger.info(f"Job {job_id} state: {srv_slicer_pb2.JobState.Name(state)}")
                    
                    if state == srv_slicer_pb2.JOB_STATE_SUCCEEDED:
                        # Job completed successfully
                        logger.info(f"Job {job_id} completed successfully")
                        break
                    elif state == srv_slicer_pb2.JOB_STATE_FAILED:
                        return {
                            "success": False,
                            "job_id": job_id,
                            "gcode_file": None,
                            "gcodevis_file": None,
                            "error": f"Job failed: {job_status.error_message}"
                        }
                    # Note: JOB_STATE_CANCELLED doesn't exist in proto, only FAILED
                    
                    # Wait before next poll
                    time.sleep(poll_interval)
                
                # Download artifacts
                result = {
                    "success": True,
                    "job_id": job_id,
                    "error": None,
                    "gcode_file": None,
                    "gcodevis_file": None
                }
                
                if not job_status.artifacts:
                    logger.warning("No artifacts returned from server")
                
                for artifact in job_status.artifacts:
                    logger.info(f"Downloading artifact: {artifact.path} ({artifact.size_bytes} bytes)")
                    
                    # Download artifact (using path, not artifact_name)
                    download_request = srv_slicer_pb2.DownloadArtifactRequest(
                        job_id=job_id,
                        path=artifact.path
                    )
                    
                    # Stream download
                    artifact_data = b""
                    for chunk_response in stub.DownloadArtifact(download_request, timeout=60):
                        artifact_data += chunk_response.data
                    
                    # Save based on artifact name/path
                    output_path = output_dir / Path(artifact.path).name
                    with open(output_path, "wb") as f:
                        f.write(artifact_data)
                    logger.info(f"Saved artifact to {output_path}")
                    
                    # Map to result keys based on filename patterns
                    if "goosli_out.gcode" in artifact.path:
                        result["gcode_file"] = output_path
                    elif "goosli_out_without_calibration" in artifact.path or "gcodevis" in artifact.path:
                        result["gcodevis_file"] = output_path
                
                logger.info(f"Downloaded {len(job_status.artifacts)} artifact(s): "
                           f"gcode={'✓' if result['gcode_file'] else '✗'}, "
                           f"gcodevis={'✓' if result['gcodevis_file'] else '✗'}")
                
                return result
                
        except grpc.RpcError as e:
            logger.error(f"GRPC error during slicing: {e.code()} - {e.details()}")
            return {
                "success": False,
                "job_id": None,
                "gcode_file": None,
                "gcodevis_file": None,
                "error": f"GRPC error: {e.code()} - {e.details()}"
            }
        except Exception as e:
            logger.error(f"Error during slicing: {e}", exc_info=True)
            return {
                "success": False,
                "job_id": None,
                "gcode_file": None,
                "gcodevis_file": None,
                "error": str(e)
            }


def slice_via_grpc(stl_filepath: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Convenience function to slice via GRPC.
    
    Args:
        stl_filepath: Path to STL file
        output_dir: Output directory for results
        
    Returns:
        Result dictionary from SlicerClient.slice_stl()
    """
    return SlicerClient.slice_stl(stl_filepath, output_dir)
