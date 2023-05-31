import math
import logging

__author__ = 'Pedro'
"""
Derived from https://github.com/payala/DeltaTuner by @payala

Delta printer least-squares calibration calculator

This calculator implements the least-squares delta calibration algorithm that RepRapFirmware has built-in.
I have provided it as a service for those not running RepRapFirmware.
You can choose to calibrate the following parameters:
"""

deg2rad = math.pi / 180


class Calibrator(object):
    initial_points = 7
    initial_factors = 6


class Matrix(object):
    base_matrix = None

    def __init__(self, rows, cols):
        self.base_matrix = [[0 for x in range(cols)] for y in range(rows)]

    def swap_rows(self, i, j):
        if i == j:
            return
        tmp = self.base_matrix[i]
        self.base_matrix[i] = self.base_matrix[j]
        self.base_matrix[j] = tmp

    def gauss_jordan(self):
        """
        Performs Gauss-Jordan elimination on a matrix with numRows rows and (numRows + 1) columns
        :return: solution vector
        """
        for i, row in enumerate(self.base_matrix):
            # Swap the rows around for stable Gauss-Jordan elimination
            self.base_matrix[i:] = sorted(self.base_matrix[i:], key=lambda col: col[i], reverse=True)

            # Use row i to eliminate the ith element from previous and subsequent rows
            v = self.base_matrix[i][i]
            r = tuple(enumerate(self.base_matrix))
            for j, srow in r[i+1:] + r[:i]:
                factor = srow[i]/v
                self.base_matrix[j] = [self.base_matrix[j][k] - self.base_matrix[i][k]*factor for k, val in
                                       enumerate(self.base_matrix[i])]
                self.base_matrix[j][i] = 0

        return [d[-1]/d[i] for i, d in enumerate(self.base_matrix)]

    def __unicode__(self):
        for row in self.base_matrix:
            print(row)


class DeltaParameters(object):
    FIRMWARE_MARLIN = "Marlin"
    FIRMWARE_MARLIN_RICH_CATTEL = "MarlinRC"
    FIRMWARE_REPETIER = "Repetier"
    FIRMWARE_REPRAPFIRMWARE = "RRF"
    FIRMWARE_SMOOTHIEWARE = "Smoothieware"

    def __init__(self, diagonal, radius, height, xstop, ystop, zstop, xadj, yadj, zadj,
                 steps_per_mm=None, firmware=None):
        self.diagonal = diagonal
        self.radius = radius
        self.homed_height = height
        self.xstop = xstop
        self.ystop = ystop
        self.zstop = zstop
        self.xadj = xadj
        self.yadj = yadj
        self.zadj = zadj

        self.steps_per_mm = steps_per_mm    # Only used for Repetier firmware

        if firmware is None:
            firmware = DeltaParameters.FIRMWARE_SMOOTHIEWARE

        if firmware == DeltaParameters.FIRMWARE_REPETIER and steps_per_mm is None:
            raise ValueError("Repetier firmware requires specifying steps_per_mm")

        self.firmware = firmware

        self.recalc()

    def transform(self, machine_pos, axis):
        return machine_pos[2] + math.sqrt(self.D2 -
                                          (machine_pos[0] - self.tower_x[axis])**2 -
                                          (machine_pos[1] - self.tower_y[axis])**2)

    def inverse_transform(self, ha, hb, hc):
        """
        Inverse kinematic method, only the z component of the result is returned.
        :param ha: x carriage height
        :param hb: y carriage height
        :param hc: z carriage height
        :return: z component of the real position
        """
        fa = self.coreFa + ha ** 2
        fb = self.coreFb + hb ** 2
        fc = self.coreFc + hc ** 2

        # Setup PQRSU such that x = -(S - uz)/P^, y = (P - Rz)/Q
        p = (self.Xbc * fa) + (self.Xca * fb) + (self.Xab * fc)
        s = (self.Ybc * fa) + (self.Yca * fb) + (self.Yab * fc)

        r = 2 * ((self.Xbc * ha) + (self.Xca * hb) + (self.Xab * hc))
        u = 2 * ((self.Ybc * ha) + (self.Yca * hb) + (self.Yab * hc))

        r2 = r ** 2
        u2 = u ** 2

        a = u2 + r2 + self.Q2
        minus_half_b = s * u + p * r + ha * self.Q2 + self.tower_x[0] * u * self.Q - self.tower_y[0] * r * self.Q
        c = (s + self.tower_x[0] * self.Q) ** 2 + (p - self.tower_y[0] * self.Q) ** 2 + (ha ** 2 - self.D2) * self.Q2

        rslt = (minus_half_b - math.sqrt(minus_half_b**2 - a * c)) / a
        if math.isnan(rslt):
            raise Exception("At least one probe point is not reachable. Please correct your "
                            "delta radius, diagonal rod length, or probe coordniates.")
        return rslt

    def recalc(self):
        self.tower_x = []
        self.tower_y = []
        self.tower_x.append(-(self.radius * math.cos((30 + self.xadj) * deg2rad)))
        self.tower_y.append(-(self.radius * math.sin((30 + self.xadj) * deg2rad)))
        self.tower_x.append(+(self.radius * math.cos((30 - self.yadj) * deg2rad)))
        self.tower_y.append(-(self.radius * math.sin((30 - self.yadj) * deg2rad)))
        self.tower_x.append(-(self.radius * math.sin(self.zadj * deg2rad)))
        self.tower_y.append(+(self.radius * math.cos(self.zadj * deg2rad)))

        self.Xbc = self.tower_x[2] - self.tower_x[1]
        self.Xca = self.tower_x[0] - self.tower_x[2]
        self.Xab = self.tower_x[1] - self.tower_x[0]
        self.Ybc = self.tower_y[2] - self.tower_y[1]
        self.Yca = self.tower_y[0] - self.tower_y[2]
        self.Yab = self.tower_y[1] - self.tower_y[0]
        self.coreFa = self.tower_x[0] ** 2 + self.tower_y[0] ** 2
        self.coreFb = self.tower_x[1] ** 2 + self.tower_y[1] ** 2
        self.coreFc = self.tower_x[2] ** 2 + self.tower_y[2] ** 2
        self.Q = 2 * (self.Xca * self.Yab - self.Xab * self.Yca)
        self.Q2 = self.Q ** 2
        self.D2 = self.diagonal ** 2

        # Calculate the base carriage height when the printer is homed
        temp_height = self.diagonal     # any sensible height will do here, probably even zero
        self.homed_carriage_height = (self.homed_height + temp_height -
                                      self.inverse_transform(temp_height, temp_height, temp_height))

    def compute_derivative(self, deriv, ha, hb, hc):
        perturb = 0.2   # perturbation amount in mm or degrees
        hi_params = DeltaParameters(self.diagonal, self.radius, self.homed_height, self.xstop,
                                    self.ystop, self.zstop, self.xadj, self.yadj, self.zadj)
        lo_params = DeltaParameters(self.diagonal, self.radius, self.homed_height, self.xstop,
                                    self.ystop, self.zstop, self.xadj, self.yadj, self.zadj)

        if deriv == 3:
            hi_params.radius += perturb
            lo_params.radius -= perturb
        elif deriv == 4:
            hi_params.xadj += perturb
            lo_params.xadj -= perturb
        elif deriv == 5:
            hi_params.yadj += perturb
            lo_params.yadj -= perturb
        elif deriv == 6:
            hi_params.diagonal += perturb
            lo_params.diagonal -= perturb

        hi_params.recalc()
        lo_params.recalc()

        z_hi = hi_params.inverse_transform(ha + perturb if deriv == 0 else ha,
                                           hb + perturb if deriv == 1 else hb,
                                           hc + perturb if deriv == 2 else hc)
        z_lo = lo_params.inverse_transform(ha - perturb if deriv == 0 else ha,
                                           hb - perturb if deriv == 1 else hb,
                                           hc - perturb if deriv == 2 else hc)

        return (z_hi - z_lo)/(2 * perturb)

    def normalise_endstop_adjustments(self):
        """
        Make the average of the endstop adjustments zero, or make all endstop corrections negative, without
        changing the individual homed carriage heights
        :return:
        """
        if self.firmware == "Marlin" or self.firmware == "MarlinRC" or self.firmware == "Repetier":
            eav = min(self.xstop, min(self.ystop, self.zstop))
        else:
            eav = (self.xstop + self.ystop + self.zstop)/3.0

        self.xstop -= eav
        self.ystop -= eav
        self.zstop -= eav
        self.homed_height += eav
        self.homed_carriage_height += eav   # No need for a full recalc, this is sufficient

    def adjust(self, num_factors, v, norm):
        """
        Perform the 3, 4, 6 or 7-factor adjustment.
        The input vector contains the following parameters in this order:
        X, Y and Z endstop adjustments
        If we are doing 4-factor adjustment, the next argument is the delta radius. Otherwise:
        X tower X position adjustment
        Y tower Y position adjustment
        Z tower Z position adjustment
        Diagonal rod length adjustment
        :return:
        """
        old_carriage_height_a = self.homed_carriage_height + self.xstop     # save for later

        # update endstop adjustments
        self.xstop += v[0]
        self.ystop += v[1]
        self.zstop += v[2]
        if norm:
            self.normalise_endstop_adjustments()

        if num_factors >= 4:
            self.radius += v[3]

            if num_factors >= 6:
                self.xadj += v[4]
                self.yadj += v[5]

                if num_factors == 7:
                    self.diagonal += v[6]

            self.recalc()

        # Adjusting the diagonal and the tower positions affects the homed carriage height
        # We need to adjust homed_height to allow for this, to get the change that was requested in
        # the endstop corrections.
        height_error = self.homed_carriage_height + self.xstop - old_carriage_height_a - v[0]
        self.homed_height -= height_error
        self.homed_carriage_height -= height_error

    def clone(self, source_deltaparams):
        self.__dict__.update(source_deltaparams.__dict__)
        self.recalc()

    def convert_outgoing_endstops(self):

        if self.firmware == self.FIRMWARE_REPRAPFIRMWARE:
            endstop_factor = 1.0
        elif self.firmware == self.FIRMWARE_REPETIER:
            endstop_factor = self.steps_per_mm
        else:
            endstop_factor = -1.0

        try:
            self.xstop *= endstop_factor
            self.ystop *= endstop_factor
            self.zstop *= endstop_factor
        except TypeError:
            raise ValueError("With Repetier firmware, steps_per_mm needs to be set in the constructor")

    def convert_incoming_endstops(self):
        endstop_factor = 1.0

        if self.firmware == self.FIRMWARE_REPRAPFIRMWARE:
            endstop_factor = 1.0
        elif self.firmware == self.FIRMWARE_REPETIER:
            endstop_factor = 1.0/self.steps_per_mm
        else:
            endstop_factor = -1.0

        try:
            self.xstop *= endstop_factor
            self.ystop *= endstop_factor
            self.zstop *= endstop_factor
        except TypeError:
            raise ValueError("With Repetier firmware, steps_per_mm needs to be set in the constructor")


class Tuner(object):
    def __init__(self, old_rod_length, old_radius, old_homed_height, old_xstop, old_ystop, old_zstop,
                 old_xpos, old_ypos, old_zpos, probe_radius=64, num_probe_points=7, num_factors=6):
        self.num_factors = num_factors
        self.num_points = num_probe_points
        self.x_bed_probe_points = []
        self.y_bed_probe_points = []
        self.z_bed_probe_points = []

        self.probe_radius = probe_radius
        self._calc_probe_points()
        self.normalise = True
        self.old_params = DeltaParameters(old_rod_length, old_radius, old_homed_height, old_xstop,
                                          old_ystop, old_zstop, old_xpos, old_ypos, old_zpos)
        self.new_params = DeltaParameters(old_rod_length, old_radius, old_homed_height, old_xstop,
                                          old_ystop, old_zstop, old_xpos, old_ypos, old_zpos)

    def set_firmware(self, firmware, steps_per_mm=None):
        if firmware in [DeltaParameters.FIRMWARE_MARLIN, DeltaParameters.FIRMWARE_MARLIN_RICH_CATTEL,
                        DeltaParameters.FIRMWARE_REPRAPFIRMWARE, DeltaParameters.FIRMWARE_SMOOTHIEWARE]:
            self.new_params.firmware = firmware
            self.old_params.firmware = firmware
        elif firmware == DeltaParameters.FIRMWARE_REPETIER:
            if steps_per_mm is None:
                raise ValueError("Repetier firmware requires specifying steps_per_mm")
            self.new_params.steps_per_mm = steps_per_mm
            self.new_params.firmware = firmware
            self.old_params.steps_per_mm = steps_per_mm
            self.old_params.firmware = firmware


    def _do_delta_calibration(self):
        """
        Runs the main delta calibration calculation.
        :return:
        """
        if self.num_factors not in [3, 4, 6, 7]:
            raise Exception("{} factors requested but only 3, 4, 6 and 7 are supported".format(self.num_factors))

        if self.num_factors > self.num_points:
            raise Exception("Need at least as many points as factors you want to calibrate")

        # Transform the probing points to motor endpoints and store them in a matrix, so that we can do
        # multiple iterations using the same data
        probe_motor_positions = Matrix(self.num_points, 3)
        corrections = [0] * self.num_points
        initial_sum_of_squares = 0.0
        for i in range(self.num_points):
            corrections[i] = 0.0

            xp = self.x_bed_probe_points[i]
            yp = self.y_bed_probe_points[i]

            machine_pos = [xp, yp, 0.0]

            probe_motor_positions.base_matrix[i][0] = self.old_params.transform(machine_pos, 0)
            probe_motor_positions.base_matrix[i][1] = self.old_params.transform(machine_pos, 1)
            probe_motor_positions.base_matrix[i][2] = self.old_params.transform(machine_pos, 2)

            initial_sum_of_squares += self.z_bed_probe_points[i] ** 2

        logging.debug("Motor positions:{}".format(probe_motor_positions))

        # Do 1 or more Newton-Raphson iterations
        expected_rms_error = 0
        for iteration in range(2):
            # Build a Nx7 matrix of derivatives with respect to xa, xb, yc, za, zb, zc, diagonal.
            derivative_matrix = Matrix(self.num_points, self.num_factors)
            for i in range(self.num_points):
                for j in range(self.num_factors):
                    derivative_matrix.base_matrix[i][j] = self.old_params.compute_derivative(
                        j,
                        probe_motor_positions.base_matrix[i][0],
                        probe_motor_positions.base_matrix[i][1],
                        probe_motor_positions.base_matrix[i][2]
                    )

            logging.debug("Derivative matrix: {}".format(derivative_matrix))

            # Now build the normal equations for least squares fitting
            normal_matrix = Matrix(self.num_factors, self.num_factors + 1)
            for i in range(self.num_factors):
                for j in range(self.num_factors):
                    temp = derivative_matrix.base_matrix[0][i] * derivative_matrix.base_matrix[0][j]
                    for k in range(1, self.num_points):
                        temp += derivative_matrix.base_matrix[k][i] * derivative_matrix.base_matrix[k][j]
                    normal_matrix.base_matrix[i][j] = temp
                temp = derivative_matrix.base_matrix[0][i] * -(self.z_bed_probe_points[0] + corrections[0])
                for k in range(1, self.num_points):
                    temp += derivative_matrix.base_matrix[k][i] * -(self.z_bed_probe_points[k] + corrections[k])
                normal_matrix.base_matrix[i][self.num_factors] = temp

            logging.debug("Normal matrix: {}".format(normal_matrix))

            solution = normal_matrix.gauss_jordan()

            for i in range(self.num_factors):
                if math.isnan(solution[i]):
                    raise Exception("Unable to calculate corrections. Please make sure "
                                    "that the bed probe points are all distinct")

            logging.debug("Solved matrix: {}".format(normal_matrix))

            # Calculate the residuals for debugging
            logging.debug("Solution: {}".format(solution))
            residuals = []
            for i in range(self.num_points):
                r = self.z_bed_probe_points[i]
                for j in range(self.num_factors):
                    r += solution[j] * derivative_matrix.base_matrix[i][j]
                residuals.append(r)

            logging.debug("Residuals: {}".format(residuals))

            if iteration == 0:
                self.new_params.clone(self.old_params)
            self.new_params.adjust(self.num_factors, solution, self.normalise)

            # Calculate the expected probe heights using the new parameters
            expected_residuals = [0] * self.num_points
            sum_of_squares = 0.0

            for i in range(self.num_points):
                for axis in range(3):
                    probe_motor_positions.base_matrix[i][axis] += solution[axis]
                new_z = self.new_params.inverse_transform(probe_motor_positions.base_matrix[i][0],
                                                          probe_motor_positions.base_matrix[i][1],
                                                          probe_motor_positions.base_matrix[i][2])
                corrections[i] = new_z
                expected_residuals[i] = self.z_bed_probe_points[i] + new_z
                sum_of_squares += expected_residuals[i] ** 2
            expected_rms_error = math.sqrt(sum_of_squares/self.num_points)
            logging.debug("Expected probe error: {}".format(expected_residuals))

            # Decide whether to do another iteration. Two is slightly better than one, but three doesn't
            # improve things. Alternatively, we could stop when the expected RMS error is only slightly
            # worse than the RMS of the residuals.
        logging.info("Calibrated {} factors using {} points, deviation before {} after {}".format(
            self.num_factors,
            self.num_points,
            math.sqrt(initial_sum_of_squares/self.num_points),
            expected_rms_error
        ))
        return (self.num_factors,
                self.num_points,
                math.sqrt(initial_sum_of_squares/self.num_points),
                expected_rms_error)

    def _calc_probe_points(self):
        """
        Calculates the probe points based on the number of points and the specified radius
        :return:
        """

        self.x_bed_probe_points = [0] * self.num_points
        self.y_bed_probe_points = [0] * self.num_points
        self.z_bed_probe_points = [0] * self.num_points

        if self.num_points == 4:
            for i in range(3):
                self.x_bed_probe_points[i] = self.probe_radius * math.sin((2*math.pi*i)/3)
                self.y_bed_probe_points[i] = self.probe_radius * math.cos((2 * math.pi * i) / 3)
            self.x_bed_probe_points[3] = 0.0
            self.y_bed_probe_points[3] = 0.0

        else:
            if self.num_points >= 7:
                for i in range(6):
                    self.x_bed_probe_points[i] = self.probe_radius * math.sin((2 * math.pi * i) / 6)
                    self.y_bed_probe_points[i] = self.probe_radius * math.cos((2 * math.pi * i) / 6)
            if self.num_points >= 10:
                for i in range(6, 9):
                    self.x_bed_probe_points[i] = self.probe_radius / 2 * math.sin((2 * math.pi * i) / 6)
                    self.y_bed_probe_points[i] = self.probe_radius / 2 * math.cos((2 * math.pi * i) / 6)
                self.x_bed_probe_points[9] = 0.0
                self.y_bed_probe_points[9] = 0.0

            else:
                self.x_bed_probe_points[6] = 0.0
                self.y_bed_probe_points[6] = 0.0

    def _generate_commands(self):
        m_665 = "M665 R{:.2f} L{:.2f}".format(self.new_params.radius, self.new_params.diagonal)
        m_666 = "M666 X{:.2f} Y{:.2f} Z{:.2f}".format(self.new_params.xstop,
                                                      self.new_params.ystop,
                                                      self.new_params.zstop)
        if self.new_params.firmware == DeltaParameters.FIRMWARE_REPRAPFIRMWARE:
            m_665 += " H{:.2f} B{:.2f} X{:.2f} Y{:.2f} Z{:.2f}".format(self.new_params.homed_height,
                                                                       self.probe_radius,
                                                                       self.new_params.xadj,
                                                                       self.new_params.yadj,
                                                                       self.new_params.zadj)
        elif self.new_params.firmware in [DeltaParameters.FIRMWARE_MARLIN,
                                          DeltaParameters.FIRMWARE_MARLIN_RICH_CATTEL]:
            m_666 += " R{:.2f} D{:.2f} H{:.2f} A{:.2f} B{:.2f} C{:.2f}".format(self.new_params.radius,
                                                                               self.new_params.diagonal,
                                                                               self.new_params.homed_height,
                                                                               self.new_params.xadj,
                                                                               self.new_params.yadj,
                                                                               self.new_params.zadj)
        elif self.new_params.firmware in [DeltaParameters.FIRMWARE_REPETIER,
                                          DeltaParameters.FIRMWARE_SMOOTHIEWARE]:
            m_665 += " D{:.2f} E{:.2f} H{:.2f} Z{:.2f}".format(self.new_params.xadj,
                                                               self.new_params.yadj,
                                                               self.new_params.zadj,
                                                               self.new_params.homed_height)

        commands = (m_665, m_666)
        if self.new_params.firmware == DeltaParameters.FIRMWARE_MARLIN:
            print("\n; Set homed height {:.2f}mm in config.h".format(self.new_params.homed_height))
            # Todo: Show the user a message instead of printing this in the command
        return commands

    def calc(self, recalc=True):
        """
        Runs the full parameter tuning calculation
        :param recalc: If False, it will not take the results of the last calculation as
        the starting conditions for the next iteration. Default: False.
        :return:
        """
        if recalc:
            self.old_params.clone(self.new_params)

        self.old_params.convert_incoming_endstops()
        rslt = self._do_delta_calibration()
        dev_before = rslt[2]
        dev_after = rslt[3]
        self.old_params.convert_outgoing_endstops()
        self.new_params.convert_outgoing_endstops()
        return [self._generate_commands(), dev_before, dev_after]


    def _copy_to_initial(self):
        self.old_params.clone(self.new_params)

    def get_probe_points(self):
        """
        Calculates and returns an array with each probe point coordinates by rows.
        [
            [ p1_x, p1_y, p1_z],
            [ p2_x, p2_y, p2_z],
            ...
            [ pn_x, pn_y, pn_z],
        ]

        z points will be zero, and should be filled with the height error at each point,
        obtained in the test.
        :return:
        """
        self._calc_probe_points()
        return [[self.x_bed_probe_points[i],
                 self.y_bed_probe_points[i],
                 self.z_bed_probe_points[i]]
                for i, p in enumerate(self.x_bed_probe_points)]

    def set_probe_errors(self, probe_points):
        """
        Sets the z component of the probe points after testing. See get_probe_points
        :param probe_points: the same bidimensional list that 'get_probe_points' returned,
        filled with the z error components obtained in the probing. Z values should be positive
        when the nozzle is too high, and negative when the nozzle is too low.
        :return:
        """

        self.z_bed_probe_points = [-probe[2] for probe in probe_points]


if __name__ == "__main__":
    m = Matrix(3, 4)
    m.base_matrix = [[1, 0, 0, 2], [2, 0, 3, 4], [3, 3, 3, 5]]
    m.gauss_jordan()
    pass
