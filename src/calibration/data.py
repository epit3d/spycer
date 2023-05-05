import csv


class CalibrationData:
    def __init__(self):
        # self.points = [None for _ in range(25)]
        self.points = []

    def writeToFile(self, filename):
        csvfile = open(filename, 'w', newline='')
        csvwriter = csv.writer(csvfile)

        print(self.points)
        for point in self.points:
            row = [f"{val:.3f}"for val in point]
            csvwriter.writerow(row)

        csvfile.close()
