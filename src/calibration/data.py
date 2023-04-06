import csv


class CalibrationData:
    def __init__(self):
        # self.points = [None for _ in range(25)]
        self.points = []

    def writeToFile(self, filename):
        csvfile = open(filename, 'w', newline='')
        csvwriter = csv.writer(csvfile)

        for point in self.points:
            csvwriter.writerow(point)
