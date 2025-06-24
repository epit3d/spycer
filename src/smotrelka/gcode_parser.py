import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class PathType(Enum):
    TRAVEL = "TRAVEL"
    SKIRT = "SKIRT"
    FILL = "FILL"
    OUTLINE_HOLES = "OUTLINE_HOLES"
    OUTLINES = "OUTLINES"
    WALLS = "WALLS"
    INNER_PATHS = "INNER_PATHS"
    LID_OUTLINES = "LID_OUTLINES"
    LID_FILL = "LID_FILL"
    LID_OUTLINE_HOLES = "LID_OUTLINE_HOLES"
    NEGATIVE_EXTRUSION = "NEGATIVE_EXTRUSION"  # New debug type
    UNKNOWN = "UNKNOWN"


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    u: float = 0.0  # rotation around X axis
    v: float = 0.0  # rotation around Z axis
    e: float = 0.0  # extrusion (absolute)


@dataclass
class PathSegment:
    start_pos: Position
    end_pos: Position
    path_type: PathType
    color: str
    is_extrusion: bool


@dataclass
class Layer:
    number: int
    segments: List[PathSegment]


class GCodeParser:
    def __init__(
        self,
        rotation_center_x=0.0,
        rotation_center_y=0.0,
        rotation_center_z=63.5,
        debug_negative_extrusion=False,
    ):
        self.colors = {
            PathType.TRAVEL: "#FFFFFF",  # white
            PathType.SKIRT: "#FF0000",  # red
            PathType.FILL: "#00FF00",  # green
            PathType.OUTLINE_HOLES: "#0000FF",  # blue
            PathType.OUTLINES: "#FFFF00",  # yellow
            PathType.UNKNOWN: "#808080",  # gray
            PathType.WALLS: "#FFA500",  # orange
            PathType.INNER_PATHS: "#800080",  # purple
            PathType.LID_OUTLINES: "#00FFFF",  # cyan
            PathType.LID_FILL: "#FFC0CB",  # pink
            PathType.LID_OUTLINE_HOLES: "#A52A2A",  # brown
            PathType.NEGATIVE_EXTRUSION: "#FF00FF",  # magenta - very visible debug color
        }

        # Rotation center point
        self.rotation_point = np.array(
            [rotation_center_x, rotation_center_y, rotation_center_z]
        )

        # Debug flags
        self.debug_negative_extrusion = debug_negative_extrusion

    def _rotation_matrix(self, axis, theta):
        """
        Return the rotation matrix associated with counterclockwise rotation about
        the given axis by theta radians.
        """
        axis = np.asarray(axis)
        axis = axis / np.sqrt(np.dot(axis, axis))
        a = np.cos(theta / 2.0)
        b, c, d = -axis * np.sin(theta / 2.0)
        aa, bb, cc, dd = a * a, b * b, c * c, d * d
        bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
        return np.array(
            [
                [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc],
            ]
        )

    def _transform_point(self, pos: Position) -> np.array:
        """Transform a point from machine coordinates to world coordinates using U and V rotations"""
        # Original point
        point = np.array([pos.x, pos.y, pos.z])

        # If no rotations, return original point
        if abs(pos.u) < 1e-6 and abs(pos.v) < 1e-6:
            return point

        # Translate to rotation center
        translated_point = point - self.rotation_point

        # Convert angles from degrees to radians
        u_rad = np.radians(pos.u)  # Rotation around Z axis
        v_rad = np.radians(pos.v)  # Rotation around X axis (incline)

        # Create rotation matrices using the general rotation function
        # Rotation around Z axis (U parameter)
        Rz = self._rotation_matrix([0, 0, 1], -u_rad)

        # Rotation around X axis (V parameter - incline)
        Rx = self._rotation_matrix([1, 0, 0], -v_rad)

        # Apply rotations: first rotation around Z (U), then incline around X (V)
        # This matches the VTK order: RotateZ then RotateX
        # Combined rotation matrix
        # R_combined = Rx @ Rz
        R_combined = Rz @ Rx

        # Apply rotation
        rotated_point = R_combined @ translated_point

        # Translate back from rotation center
        world_point = rotated_point + self.rotation_point

        return world_point

    def _is_special_comment(self, line: str) -> bool:
        special_prefixes = [";LAYER:"]
        layer_part_prefixes = [
            ";SKIRT",
            ";FILL",
            ";OUTLINE_HOLES",
            ";OUTLINES",
            ";INNER_PATHS",
            ";LID_OUTLINES",
            ";LID_FILL",
            ";LID_OUTLINE_HOLES",
        ]
        special_prefixes += layer_part_prefixes
        special_prefixes += [";SUPPORT_" + part[1:] for part in layer_part_prefixes]

        rotation_suffixes = ["rotation-hack", "rotation", "incline-hack", "incline"]

        return any(line.startswith(prefix) for prefix in special_prefixes) or any(
            line.endswith(suffix) for suffix in rotation_suffixes
        )

    def _parse_rotation_value(self, args):
        """Parse rotation value from arguments list"""
        # Assuming the rotation value is the second argument (after the command)
        if len(args) > 1:
            try:
                return float(args[1])
            except (ValueError, IndexError):
                return 0.0
        return 0.0

    def parse(self, gcode_content: str) -> List[Layer]:
        lines = gcode_content.strip().split("\n")
        print(f"Parsing {len(lines)} lines of G-code")
        layers = []
        current_layer = None
        current_path_type = PathType.UNKNOWN
        current_pos = Position()

        # Debug counters
        negative_extrusion_count = 0

        for line_num, line in enumerate(lines):
            line = line.strip()
            # Skip empty lines
            if not line:
                continue

            if line.startswith(";") and self._is_special_comment(line):
                # Handle special comments
                if line.startswith(";LAYER:"):
                    layer_num = self._extract_layer_number(line)
                    if current_layer is not None:
                        # print(f"Completed layer {current_layer.number} with {len(current_layer.segments)} segments")
                        layers.append(current_layer)
                    current_layer = Layer(layer_num, [])
                    # print(f"Starting layer {layer_num} at line {line_num}")
                elif line.endswith("rotation-hack"):
                    # Handle rotation-hack: U value passed in comment section
                    try:
                        parts = line.split(";")
                        if len(parts) >= 3:
                            args = parts[1].split(" ")
                            rotation_value = self._parse_rotation_value(args)
                            current_pos.u = rotation_value
                            print(
                                f"Rotation-hack update: U={current_pos.u:.3f}° at line {line_num}"
                            )
                    except Exception as e:
                        print(
                            f"Warning: Failed to parse rotation-hack at line {line_num}: {e}"
                        )
                elif line.endswith("rotation"):
                    # Handle standard rotation
                    try:
                        parts = line.split(";")
                        if len(parts) >= 2:
                            args = parts[1].split(" ")
                            rotation_value = self._parse_rotation_value(args)
                            current_pos.u = rotation_value
                            print(
                                f"Rotation update: U={current_pos.u:.3f}° at line {line_num}"
                            )
                    except Exception as e:
                        print(
                            f"Warning: Failed to parse rotation at line {line_num}: {e}"
                        )
                elif line.endswith("incline-hack"):
                    # Handle incline-hack: V value passed in comment section
                    try:
                        parts = line.split(";")
                        if len(parts) >= 3:
                            args = parts[1].split(" ")
                            incline_value = self._parse_rotation_value(args)
                            current_pos.v = incline_value
                            print(
                                f"Incline-hack update: V={current_pos.v:.3f}° at line {line_num}"
                            )
                    except Exception as e:
                        print(
                            f"Warning: Failed to parse incline-hack at line {line_num}: {e}"
                        )
                elif line.endswith("incline"):
                    # Handle standard incline
                    try:
                        parts = line.split(";")
                        if len(parts) >= 2:
                            args = parts[1].split(" ")
                            incline_value = self._parse_rotation_value(args)
                            current_pos.v = incline_value
                            print(
                                f"Incline update: V={current_pos.v:.3f}° at line {line_num}"
                            )
                    except Exception as e:
                        print(
                            f"Warning: Failed to parse incline at line {line_num}: {e}"
                        )
                elif line.startswith(";"):
                    path_type = self._extract_path_type(line)
                    if path_type:
                        current_path_type = path_type
                        # print(f"Changed path type to {path_type} at line {line_num}")
                continue

            # Parse G0/G1 commands
            if line.startswith("G0") or line.startswith("G1"):
                is_extrusion = line.startswith("G1")
                new_pos = self._parse_movement_command(line, current_pos)

                # Validate positions are finite
                if not self._is_valid_position(new_pos):
                    print(f"Warning: Invalid position at line {line_num}: {line}")
                    continue

                if current_layer is not None:
                    # Transform positions to world coordinates
                    start_world = self._transform_point(current_pos)
                    end_world = self._transform_point(new_pos)

                    # Create positions with transformed coordinates
                    start_pos_transformed = Position(
                        x=start_world[0],
                        y=start_world[1],
                        z=start_world[2],
                        u=current_pos.u,
                        v=current_pos.v,
                        e=current_pos.e,
                    )
                    end_pos_transformed = Position(
                        x=end_world[0],
                        y=end_world[1],
                        z=end_world[2],
                        u=new_pos.u,
                        v=new_pos.v,
                        e=new_pos.e,
                    )

                    # Check for negative extrusion
                    extrusion_diff = new_pos.e - current_pos.e
                    has_negative_extrusion = (
                        self.debug_negative_extrusion
                        and is_extrusion
                        and extrusion_diff < -1e-6
                    )  # Small tolerance for floating point

                    # Determine path type and color
                    if line.startswith("G0"):
                        segment_type = PathType.TRAVEL
                        color = self.colors[PathType.TRAVEL]
                    elif has_negative_extrusion:
                        # Override path type for negative extrusion
                        segment_type = PathType.NEGATIVE_EXTRUSION
                        color = self.colors[PathType.NEGATIVE_EXTRUSION]
                        negative_extrusion_count += 1
                        layer_info = (
                            f"Layer {current_layer.number}"
                            if current_layer
                            else "No layer"
                        )
                        print(
                            f"DEBUG: Negative extrusion detected at line {line_num} ({layer_info}): E diff = {extrusion_diff:.6f}"
                        )
                    else:
                        segment_type = current_path_type
                        color = self.colors[current_path_type]

                    segment = PathSegment(
                        start_pos=start_pos_transformed,
                        end_pos=end_pos_transformed,
                        path_type=segment_type,
                        color=color,
                        is_extrusion=is_extrusion,  # and new_pos.e > current_pos.e
                    )
                    current_layer.segments.append(segment)

                current_pos = new_pos

        # Add the last layer if it exists
        if current_layer is not None:
            print(
                f"Completed final layer {current_layer.number} with {len(current_layer.segments)} segments"
            )
            layers.append(current_layer)

        print(f"Parsing complete: {len(layers)} layers total")
        if self.debug_negative_extrusion and negative_extrusion_count > 0:
            print(
                f"DEBUG: Found {negative_extrusion_count} segments with negative extrusion (shown in magenta)"
            )

        return layers

    def _is_valid_position(self, pos: Position) -> bool:
        """Check if position has valid (finite) coordinates"""
        return all(
            isinstance(val, (int, float)) and np.isfinite(val)
            for val in [pos.x, pos.y, pos.z, pos.u, pos.v, pos.e]
        )

    def _extract_layer_number(self, line: str) -> int:
        match = re.search(r";LAYER:(\d+)", line)
        return int(match.group(1)) if match else 0

    def _extract_path_type(self, line: str) -> Optional[PathType]:
        if ";SKIRT" in line:
            return PathType.SKIRT
        elif ";FILL" in line:
            return PathType.FILL
        elif ";OUTLINE_HOLES" in line:
            return PathType.OUTLINE_HOLES
        elif ";OUTLINES" in line:
            return PathType.OUTLINES
        elif ";WALLS" in line:
            return PathType.WALLS
        elif ";INNER_PATHS" in line:
            return PathType.INNER_PATHS
        elif ";LID_OUTLINES" in line:
            return PathType.LID_OUTLINES
        elif ";LID_FILL" in line:
            return PathType.LID_FILL
        elif ";LID_OUTLINE_HOLES" in line:
            return PathType.LID_OUTLINE_HOLES
        elif ";TRAVEL" in line:
            return PathType.TRAVEL
        else:
            # If no known path type is found, return None
            if ";" in line:
                return PathType.UNKNOWN
            else:
                # If it's a G-code command without a comment, treat it as travel
                return PathType.TRAVEL if line.startswith("G0") else None
        return None

    def _parse_movement_command(self, line: str, current_pos: Position) -> Position:
        new_pos = Position(**current_pos.__dict__)

        # Track if U or V values changed for debugging
        u_changed = False
        v_changed = False

        # Parse X, Y, Z, U, V, E coordinates
        for coord in ["X", "Y", "Z", "U", "V", "E"]:
            pattern = rf"{coord}([-+]?\d*\.?\d+)"
            match = re.search(pattern, line)
            if match:
                value = float(match.group(1))
                old_value = getattr(new_pos, coord.lower())
                setattr(new_pos, coord.lower(), value)

                # Track changes in rotation values
                if coord == "U" and abs(value - old_value) > 1e-6:
                    u_changed = True
                elif coord == "V" and abs(value - old_value) > 1e-6:
                    v_changed = True

        # Debug output for rotation changes
        if u_changed or v_changed:
            print(
                f"Rotation update: U={new_pos.u:.3f}° V={new_pos.v:.3f}° (U changed: {u_changed}, V changed: {v_changed})"
            )

        return new_pos


def parse_gcode_file(
    filepath: str,
    rotation_center_x=0.0,
    rotation_center_y=0.0,
    rotation_center_z=63.5,
    debug_negative_extrusion=False,
) -> List[Layer]:
    """Convenience function to parse a G-code file."""
    parser = GCodeParser(
        rotation_center_x,
        rotation_center_y,
        rotation_center_z,
        debug_negative_extrusion,
    )
    with open(filepath, "r") as f:
        content = f.read()
    return parser.parse(content)


def parse_gcode_string(
    gcode_content: str,
    rotation_center_x=0.0,
    rotation_center_y=0.0,
    rotation_center_z=63.5,
    debug_negative_extrusion=False,
) -> List[Layer]:
    """Convenience function to parse G-code from a string."""
    parser = GCodeParser(
        rotation_center_x,
        rotation_center_y,
        rotation_center_z,
        debug_negative_extrusion,
    )
    return parser.parse(gcode_content)
