import csv
from math import exp, log, e as EULER


def read_csv_as_dict(csv_file) -> dict[str, list[str]]:
    """
    Reads a CSV file into a dictionary mapping the first column of each row to the rest of the row.
    """
    data = {}

    with open(csv_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            key = row[0]
            values = row[1:]
            data[key] = values

    return data


def logistic00(
    x: float, fit_to_point: tuple[float, float] = (1.0, EULER / (EULER + 1.0))
) -> float:
    """
    Logistic function with range (-1, 1), passing through (0, 0) and (fit_to_point[0], fit_to_point[1]).
    """
    if abs(fit_to_point[1]) >= 1:
        raise ValueError(
            "The second value of fit_to_point must be strictly between 0 and 1"
        )
    # Determine the constant `a` to fit logistic curve through the given point
    a = -log((1 - fit_to_point[1]) / (1 + fit_to_point[1])) / fit_to_point[0]
    return 2 / (1 + exp(-a * x)) - 1
