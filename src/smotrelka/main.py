import numpy as np
import pyvista as pv
import argparse
from src.smotrelka.gcode_parser import parse_gcode_file, PathType
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pyvistaqt import BackgroundPlotter

class GCodeVisualizer:
    def __init__(self, layers, default_opacity=0.8, plotter=None):
        self.layers = layers
        self.current_layer_idx = 0
        self.plotter = plotter
        self.cached_meshes = {}  # Cache meshes to avoid regenerating
        self.layer_actors = {}  # Track actors for each layer
        
        # Box dimensions configuration
        self.default_width = 0.4  # Default line width in mm
        self.layer_height = 0.2   # Layer height in mm
        
        # Rendering options
        self.default_opacity = default_opacity
        
        # Threading for mesh generation
        self._mesh_lock = threading.Lock()
    
    def preload_all_meshes(self, max_workers=None):
        """Preload all meshes with progress display using multithreading"""
        if max_workers is None:
            import os
            max_workers = min(os.cpu_count() or 1, len(self.layers))
        
        print(f"\nPreloading meshes for {len(self.layers)} layers using {max_workers} threads...")
        print("This may take a while depending on the complexity of your model.")
        print("-" * 60)
        
        successful_layers = 0
        failed_layers = 0
        completed_count = 0
        
        def process_layer(layer):
            """Process a single layer and return (layer_number, mesh)"""
            try:
                # Create a temporary instance without the lock for thread-local processing
                mesh = self._create_layer_mesh_unlocked(layer)
                return layer.number, mesh
            except Exception as e:
                print(f"\nError processing layer {layer.number}: {e}")
                return layer.number, None
        
        start_time = time.time()
        
        # Use ProcessPoolExecutor instead of ThreadPoolExecutor for CPU-bound tasks
        from concurrent.futures import ProcessPoolExecutor
        
        # For CPU-bound mesh generation, processes can be more efficient than threads
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_layer = {executor.submit(self._process_layer_standalone, layer): layer for layer in self.layers}
                
                # Process completed tasks as they finish
                for future in as_completed(future_to_layer):
                    layer_number, mesh = future.result()
                    
                    # Thread-safe update of cache
                    with self._mesh_lock:
                        self.cached_meshes[layer_number] = mesh
                        
                    completed_count += 1
                    
                    if mesh is not None:
                        successful_layers += 1
                    else:
                        failed_layers += 1
                    
                    # Update progress bar
                    progress = completed_count / len(self.layers) * 100
                    bar_length = 40
                    filled_length = int(bar_length * completed_count // len(self.layers))
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    
                    elapsed_time = time.time() - start_time
                    if completed_count > 0:
                        eta = (elapsed_time / completed_count) * (len(self.layers) - completed_count)
                        eta_str = f"ETA: {eta:.1f}s"
                    else:
                        eta_str = "ETA: --"
                    
                    layers_per_sec = completed_count / elapsed_time if elapsed_time > 0 else 0
                    print(f"\r[{bar}] {progress:.1f}% - {completed_count}/{len(self.layers)} - {eta_str} - {layers_per_sec:.1f} layers/s", 
                          end='', flush=True)
        
        except Exception as e:
            print(f"\nProcessPoolExecutor failed, falling back to ThreadPoolExecutor: {e}")
            # Fallback to ThreadPoolExecutor
            # with ThreadPoolExecutor(max_workers=max_workers) as executor:
            #     # Submit all tasks
            #     future_to_layer = {executor.submit(process_layer, layer): layer for layer in self.layers}
                
            #     # Process completed tasks as they finish
            #     for future in as_completed(future_to_layer):
            #         layer_number, mesh = future.result()
                    
            #         # Thread-safe update of cache
            #         with self._mesh_lock:
            #             self.cached_meshes[layer_number] = mesh
                        
            #         completed_count += 1
                    
            #         if mesh is not None:
            #             successful_layers += 1
            #         else:
            #             failed_layers += 1
                    
            #         # Update progress bar
            #         progress = completed_count / len(self.layers) * 100
            #         bar_length = 40
            #         filled_length = int(bar_length * completed_count // len(self.layers))
            #         bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    
            #         elapsed_time = time.time() - start_time
            #         if completed_count > 0:
            #             eta = (elapsed_time / completed_count) * (len(self.layers) - completed_count)
            #             eta_str = f"ETA: {eta:.1f}s"
            #         else:
            #             eta_str = "ETA: --"
                    
            #         print(f"\r[{bar}] {progress:.1f}% - {completed_count}/{len(self.layers)} - {eta_str}", 
            #               end='', flush=True)
        
        elapsed_time = time.time() - start_time
        print()  # New line after progress bar
        print("-" * 60)
        print(f"Preloading complete in {elapsed_time:.1f} seconds!")
        print(f"✓ Successfully loaded: {successful_layers} layers")
        if failed_layers > 0:
            print(f"✗ Failed to load: {failed_layers} layers")
        print(f"Total meshes in cache: {len(self.cached_meshes)}")
        print(f"Average processing time: {elapsed_time/len(self.layers):.2f}s per layer")
        print(f"Processing rate: {len(self.layers)/elapsed_time:.1f} layers/second")
        print()
    
    @staticmethod
    def _process_layer_standalone(layer):
        """Standalone function for ProcessPoolExecutor"""
        # Create a temporary visualizer instance for this process
        temp_visualizer = GCodeVisualizer([layer])
        temp_visualizer.cached_meshes = {}  # Fresh cache
        mesh = temp_visualizer._create_layer_mesh_unlocked(layer)
        return layer.number, mesh

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple (0-255)"""
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    
    def _create_layer_mesh(self, layer):
        """Create meshes for a single layer (thread-safe version)"""
        with self._mesh_lock:
            return self._create_layer_mesh_unlocked(layer)
    
    def _create_layer_mesh_unlocked(self, layer):
        """Create meshes for a single layer (without thread lock)"""
        # Check cache first
        if layer.number in self.cached_meshes:
            return self.cached_meshes[layer.number]
        
        # Filter out travel paths and very short segments
        valid_segments = []
        negative_extrusion_segments = []
        
        for segment in layer.segments:
            # Collect negative extrusion segments separately for debugging
            if segment.path_type == PathType.NEGATIVE_EXTRUSION:
                negative_extrusion_segments.append(segment)
                continue
                
            # Skip travel paths entirely
            if segment.path_type == PathType.TRAVEL:
                continue
                
            # Skip very short segments
            start_point = [segment.start_pos.x, segment.start_pos.y, segment.start_pos.z]
            end_point = [segment.end_pos.x, segment.end_pos.y, segment.end_pos.z]
            distance = np.linalg.norm(np.array(end_point) - np.array(start_point))
            
            if distance >= 1e-3:  # Only keep segments with reasonable length
                valid_segments.append(segment)
            else:
                valid_segments.append(segment)  # Keep very short segments for debugging
        
        # Add negative extrusion segments back (don't filter by length for debugging)
        valid_segments.extend(negative_extrusion_segments)
        
        if negative_extrusion_segments:
            print(f"Layer {layer.number}: Found {len(negative_extrusion_segments)} negative extrusion segments")
        
        if len(valid_segments) < 1:
            # Don't cache here in unlocked version
            return None
        
        # Split into chunks of max_capacity segments
        max_capacity = 2000
        meshes = []
        
        for chunk_start in range(0, len(valid_segments), max_capacity):
            chunk_end = min(chunk_start + max_capacity, len(valid_segments))
            segment_chunk = valid_segments[chunk_start:chunk_end]
            
            mesh = self._create_chunk_mesh(segment_chunk, layer.number, len(meshes))
            if mesh is not None:
                meshes.append(mesh)
        
        if not meshes:
            return None
        
        # Combine all chunks into one mesh
        if len(meshes) == 1:
            combined_mesh = meshes[0]
        else:
            combined_mesh = meshes[0]
            for mesh in meshes[1:]:
                combined_mesh = combined_mesh + mesh  # PyVista mesh concatenation
        
        return combined_mesh
    
    def _create_chunk_mesh(self, segments, layer_num, chunk_idx):
        """Create a mesh for a chunk of segments using optimized box generation"""
        if len(segments) < 1:
            return None
            
        # Pre-allocate arrays for better performance
        all_points = []
        all_cells = []
        all_colors = []
        
        current_point_index = 0
        
        for segment in segments:
            # Calculate box dimensions
            start_point = np.array([segment.start_pos.x, segment.start_pos.y, segment.start_pos.z])
            end_point = np.array([segment.end_pos.x, segment.end_pos.y, segment.end_pos.z])
            
            # Calculate length (distance between points)
            direction_vec = end_point - start_point
            length = np.linalg.norm(direction_vec)
            if length < 1e-6:  # Skip very short segments
                length = 1.0  # Default length to avoid division by zero
                direction_vec = np.array([1.0, 0.0, 0.0])  # Default direction to avoid NaN

                # skip if the type is not debug for negative extrusion
                if segment.path_type != PathType.NEGATIVE_EXTRUSION:
                    continue
                # continue
            
            direction = direction_vec / length  # Normalize
            
            # Calculate width based on extrusion or path type
            if segment.path_type == PathType.NEGATIVE_EXTRUSION:
                # Make negative extrusion segments MUCH more visible
                width = self.default_width * 5   # 5x width for visibility
                height = self.layer_height * 5   # 5x height for visibility
                print(f"Creating large negative extrusion box: width={width:.3f}, height={height:.3f}, length={length:.3f}")
            elif segment.is_extrusion and segment.end_pos.e > segment.start_pos.e:
                eOff = segment.end_pos.e - segment.start_pos.e
                filament_diameter = 1.75  # Default filament diameter
                area = np.pi * (filament_diameter / 2) ** 2
                width = (eOff * area) / (self.layer_height * length)
                width = max(0.05, min(2.0, width))  # Clamp between reasonable values
                height = self.layer_height
            else:
                width = self.default_width
                height = self.layer_height
            
            # Calculate center position
            center = (start_point + end_point) / 2
            
            # Create box vertices directly (much faster than pv.Box + rotation)
            box_points = self._create_box_points(center, length, width, height, direction)
            
            if box_points is not None:
                # Add points
                all_points.append(box_points)
                
                # Add hexahedron cell (8 vertices per box)
                # Offset indices by current_point_index
                cell_indices = np.arange(8) + current_point_index
                all_cells.append(cell_indices)
                
                # Add color for this box
                color = self._hex_to_rgb(segment.color)
                all_colors.append(color)
                
                current_point_index += 8
        
        if not all_points:
            return None
        
        # Combine all box data into single mesh
        try:
            # Combine all points
            combined_points = np.vstack(all_points)
            
            # Create cells array in PyVista format
            # Each cell: [n_points, point0, point1, ..., pointN]
            cells_list = []
            for cell_indices in all_cells:
                cells_list.extend([8] + cell_indices.tolist())  # 8 points per hexahedron
            
            combined_cells = np.array(cells_list, dtype=np.int32)
            combined_colors = np.array(all_colors, dtype=np.uint8)
            
            # Create cell types array (VTK_HEXAHEDRON = 12)
            cell_types = np.full(len(all_cells), 12, dtype=np.uint8)
            
            # Create mesh using the correct PyVista format
            combined_mesh = pv.UnstructuredGrid(combined_cells, cell_types, combined_points)
            combined_mesh.cell_data['colors'] = combined_colors
            
            return combined_mesh
            
        except Exception as e:
            print(f"Layer {layer_num}, Chunk {chunk_idx}: Failed to create optimized mesh: {e}")
            return None
    
    def _create_box_points(self, center, length, width, height, direction):
        """Create box vertices directly without PyVista operations"""
        try:
            # Create local coordinate system
            # direction is already normalized
            up = np.array([0, 0, 1])
            
            # Handle case where direction is parallel to up vector
            if abs(np.dot(direction, up)) > 0.9:
                up = np.array([0, 1, 0])
            
            # Create orthonormal basis
            right = np.cross(direction, up)
            right = right / np.linalg.norm(right)
            up = np.cross(right, direction)
            up = up / np.linalg.norm(up)
            
            # Box vertices in local coordinates
            half_length = length / 2
            half_width = width / 2
            half_height = height / 2
            
            local_vertices = np.array([
                [-half_length, -half_width, -half_height],  # 0
                [ half_length, -half_width, -half_height],  # 1
                [ half_length,  half_width, -half_height],  # 2
                [-half_length,  half_width, -half_height],  # 3
                [-half_length, -half_width,  half_height],  # 4
                [ half_length, -half_width,  half_height],  # 5
                [ half_length,  half_width,  half_height],  # 6
                [-half_length,  half_width,  half_height]   # 7
            ])
            
            # Transform to world coordinates
            transform_matrix = np.column_stack([direction, right, up])
            world_vertices = np.dot(local_vertices, transform_matrix.T) + center
            
            return world_vertices
            
        except Exception as e:
            print(f"Failed to create box points: {e}")
            return None
    
    def _create_box_geometry(self, center, length, width, height, direction):
        """Legacy method - updated to use new format"""
        points = self._create_box_points(center, length, width, height, direction)
        if points is not None:
            # Return points and a simple cell definition
            cells = np.array([8, 0, 1, 2, 3, 4, 5, 6, 7], dtype=np.int32)
            return points, [cells]
        return None, None
    
    def _get_opacity_for_path_type(self, path_type):
        """Get opacity based on path type for better visibility"""
        if path_type == PathType.NEGATIVE_EXTRUSION:
            return 1.0  # Fully opaque for debugging
        elif path_type == PathType.TRAVEL:
            return self.default_opacity * 0.3  # Very transparent
        elif path_type in [PathType.FILL, PathType.WALLS, PathType.OUTLINES]:
            return self.default_opacity * 0.5  # Normal opacity for main features
        else:
            return self.default_opacity * 0.7  # Slightly more transparent for other types

    def _update_display(self):
        """Update the display for the current layer and all layers below"""
        # Clear actors but preserve the plotter
        self.plotter.clear_actors()
        self.layer_actors.clear()
        
        if 0 <= self.current_layer_idx < len(self.layers):
            # Show all layers from 0 to current_layer_idx (inclusive)
            for layer_idx in range(self.current_layer_idx + 1):
                layer = self.layers[layer_idx]
                mesh = self._create_layer_mesh(layer)
                
                if mesh is not None:
                    # Determine opacity based on path types in this layer
                    layer_path_types = [seg.path_type for seg in layer.segments]
                    has_negative_extrusion = PathType.NEGATIVE_EXTRUSION in layer_path_types
                    
                    # # Use different opacity for layers with negative extrusion
                    # if has_negative_extrusion:
                    #     opacity = 1.0  # Fully opaque for debug visibility
                    #     print(f"Layer {layer.number}: Contains negative extrusion - rendering fully opaque")
                    # else:
                    opacity = self.default_opacity
                    
                    # Always try to render with colors first if available
                    if hasattr(mesh, 'cell_data') and 'colors' in mesh.cell_data:
                        try:
                            # Render as colored surface with transparency
                            actor = self.plotter.add_mesh(
                                mesh,
                                scalars='colors',
                                rgb=True,
                                show_edges=False,
                                lighting=True,
                                smooth_shading=True,
                                opacity=opacity,
                                name=f'layer_{layer.number}'
                            )
                        except Exception as e:
                            print(f"Layer {layer.number}: Color rendering failed: {e}, falling back to gray")
                            # Fallback to gray if color rendering fails
                            actor = self.plotter.add_mesh(
                                mesh,
                                color='gray',
                                show_edges=False,
                                lighting=True,
                                opacity=opacity,
                                name=f'layer_{layer.number}'
                            )
                    else:
                        print(f"Layer {layer.number}: No color data available, using gray")
                        # Render as solid color surface
                        actor = self.plotter.add_mesh(
                            mesh,
                            color='gray',
                            show_edges=False,
                            lighting=True,
                            opacity=opacity,
                            name=f'layer_{layer.number}'
                        )
                    
                    self.layer_actors[layer.number] = actor
            
            # Add layer info text
            current_layer = self.layers[self.current_layer_idx]
            layer_info = f"Layer {current_layer.number} ({self.current_layer_idx + 1}/{len(self.layers)})"
            segment_count = len(current_layer.segments)
            layer_info += f"\nSegments: {segment_count}"
            layer_info += f"\nShowing layers 0-{self.current_layer_idx}"
            self.plotter.add_text(layer_info, position='upper_left', font_size=12, name='layer_info')
        
        # Force a render update
        self.plotter.render()

    def _add_layer(self, layer_idx):
        """Add a single layer to the display"""
        if 0 <= layer_idx < len(self.layers):
            layer = self.layers[layer_idx]
            
            # Skip if already displayed
            if layer.number in self.layer_actors:
                return
                
            mesh = self._create_layer_mesh(layer)
            
            if mesh is not None:
                # Determine opacity based on path types in this layer
                layer_path_types = [seg.path_type for seg in layer.segments]
                has_negative_extrusion = PathType.NEGATIVE_EXTRUSION in layer_path_types
                opacity = 1.0 if has_negative_extrusion else self.default_opacity
                
                # Always try to render with colors first if available
                if hasattr(mesh, 'cell_data') and 'colors' in mesh.cell_data:
                    try:
                        actor = self.plotter.add_mesh(
                            mesh,
                            scalars='colors',
                            rgb=True,
                            show_edges=False,
                            lighting=True,
                            smooth_shading=True,
                            opacity=opacity,
                            name=f'layer_{layer.number}'
                        )
                    except Exception as e:
                        print(f"Layer {layer.number}: Color rendering failed: {e}, falling back to white")
                        # Fallback to white if color rendering fails
                        actor = self.plotter.add_mesh(
                            mesh,
                            color='white',
                            line_width=2,
                            opacity=opacity,
                            name=f'layer_{layer.number}_lines'
                        )
                else:
                    # Simple line rendering fallback
                    actor = self.plotter.add_mesh(
                        mesh,
                        color='white',
                        line_width=2,
                        opacity=opacity,
                        name=f'layer_{layer.number}_lines'
                    )
                self.layer_actors[layer.number] = actor
    
    def _remove_layers_above(self, max_layer_idx):
        """Remove all layers above the specified index"""
        layers_to_remove = []
        for layer_idx in range(max_layer_idx + 1, len(self.layers)):
            layer = self.layers[layer_idx]
            if layer.number in self.layer_actors:
                layers_to_remove.append(layer.number)
        
        for layer_num in layers_to_remove:
            actor = self.layer_actors[layer_num]
            self.plotter.remove_actor(actor)
            del self.layer_actors[layer_num]
    
    def _update_layer_info(self):
        """Update just the layer info text"""
        # Remove existing layer info
        self.plotter.remove_actor('layer_info')
        
        if 0 <= self.current_layer_idx < len(self.layers):
            current_layer = self.layers[self.current_layer_idx]
            layer_info = f"Layer {current_layer.number} ({self.current_layer_idx + 1}/{len(self.layers)})"
            segment_count = len(current_layer.segments)
            layer_info += f"\nSegments: {segment_count}"
            layer_info += f"\nShowing layers 0-{self.current_layer_idx}"
            self.plotter.add_text(layer_info, position='upper_left', font_size=12, name='layer_info')

    def _next_layer(self):
        """Move to next layer"""
        if self.current_layer_idx < len(self.layers) - 1:
            self.current_layer_idx += 1
            # Only add the new layer, don't re-render everything
            self._add_layer(self.current_layer_idx)
            self._update_layer_info()
            self.plotter.render()
    
    def _prev_layer(self):
        """Move to previous layer"""
        if self.current_layer_idx > 0:
            # Remove layers above the new current layer
            self._remove_layers_above(self.current_layer_idx - 1)
            self.current_layer_idx -= 1
            self._update_layer_info()
            self.plotter.render()

    def _key_press_callback(self, key):
        """Handle key press events"""
        if key.lower() == 'up' or key.lower() == 'k':
            self._next_layer()
        elif key.lower() == 'down' or key.lower() == 'j':
            self._prev_layer()
        elif key.lower() == 'q':
            self.plotter.close()
    
    def show(self, preload=True, preload_threads=None, show_all_layers=False):
        """Display the visualizer"""
        if not self.layers:
            print("No layers to display")
            return
        
        # Preload all meshes first if requested
        if preload:
            self.preload_all_meshes(max_workers=preload_threads)
            
            # Filter out layers that failed to load
            valid_layer_numbers = [num for num, mesh in self.cached_meshes.items() if mesh is not None]
            
            if not valid_layer_numbers:
                print("No valid meshes were created. Cannot start visualizer.")
                return
            
            print(f"Starting visualizer with {len(valid_layer_numbers)} valid layers...")
            
            # When preloaded, show all layers by default
            show_all_layers = True
        else:
            print("Starting visualizer with on-demand mesh loading...")
        
        # self.plotter = BackgroundPlotter()
        
        # Add key event handlers
        self.plotter.add_key_event('Up', self._next_layer)
        self.plotter.add_key_event('Down', self._prev_layer)
        self.plotter.add_key_event('k', self._next_layer)
        self.plotter.add_key_event('j', self._prev_layer)
        self.plotter.add_key_event('q', lambda: self.plotter.close())
        
        # If showing all layers, set current layer to the last one
        if show_all_layers:
            self.current_layer_idx = len(self.layers) - 1

        # Initial display
        self._update_display()

        # Set camera focal point to the model center for better interaction
        try:
            # Gather all points from all cached meshes
            all_points = []
            for mesh in self.cached_meshes.values():
                if mesh is not None:
                    all_points.append(mesh.points)
            if all_points:
                all_points = np.vstack(all_points)
                center = all_points.mean(axis=0)
                self.plotter.camera.focal_point = center.tolist()
                # Optionally, move the camera back a bit from the center
                position = center + np.array([0, -max(50, (all_points[:,1].max() - all_points[:,1].min())), 30])
                self.plotter.camera.position = position.tolist()
        except Exception as e:
            print(f"Could not set camera focal point: {e}")

        # Add instructions
        instructions = "Controls:\n↑/K: Next layer\n↓/J: Previous layer\nQ: Quit"
        if preload:
            instructions += f"\n(Preloaded - showing all {len(self.layers)} layers)"
        else:
            instructions += "\n(On-demand loading)"
        self.plotter.add_text(instructions, position='lower_right', font_size=10, name='instructions')
        
        # Set camera to a good initial position
        self.plotter.camera_position = 'iso'
        
        self.plotter.show()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='G-code Layer Visualizer')
    parser.add_argument('--no-preload', action='store_true', 
                       help='Disable preloading (faster startup, slower navigation)')
    parser.add_argument('--threads', type=int, default=None,
                       help='Number of threads to use for preloading (default: auto-detect CPU cores)')
    parser.add_argument('--opacity', type=float, default=0.8,
                       help='Default opacity for meshes (0.0-1.0, default: 0.8)')
    parser.add_argument('--debug-negative-extrusion', action='store_true',
                       help='Enable debugging of negative extrusion segments (shown in magenta)')
    parser.add_argument('--gcode', type=str, default=None,
                       help='Path to the G-code file to load (overrides default)')
    args = parser.parse_args()

    from consts import GCODE_PATH

    # Determine which G-code file to use
    gcode_path = args.gcode if args.gcode else GCODE_PATH

    try:
        print(f"Parsing G-code file: {gcode_path}")
        layers = parse_gcode_file(gcode_path, debug_negative_extrusion=args.debug_negative_extrusion)
        
        if not layers:
            print("No layers found in the G-code file")
            return
        
        print(f"Found {len(layers)} layers")
        
        # Display statistics
        total_segments = sum(len(layer.segments) for layer in layers)
        print(f"Total segments: {total_segments}")
        
        # Filter out empty layers
        non_empty_layers = [layer for layer in layers if layer.segments]
        print(f"Non-empty layers: {len(non_empty_layers)}")
        
        if not non_empty_layers:
            print("No layers with segments found")
            return
        
        # Preload is now enabled by default
        preload_enabled = not args.no_preload
        
        if preload_enabled:
            print("Preload mode enabled (default) - all meshes will be loaded and full model displayed")
            if args.threads:
                print(f"Using {args.threads} threads for preloading")
        else:
            print("On-demand mode - meshes will be loaded as needed (faster startup)")
        
        print(f"Using opacity: {args.opacity}")
        if args.debug_negative_extrusion:
            print("Negative extrusion debugging enabled - segments will be shown in magenta")
        
        visualizer = GCodeVisualizer(non_empty_layers, default_opacity=args.opacity)
        visualizer.show(preload=preload_enabled, preload_threads=args.threads)
        
    except FileNotFoundError:
        print(f"Error: File '{gcode_path}' not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
