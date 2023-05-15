from src.printer.delta import DeltaParams
from src.printer.escher import Escher, Point


def test_Escher_6_factors():
    factorsNumber = 6

    dp = DeltaParams()
    print(dp.toString())

    points = [
        (  0,  90,   0.9),  # noqa
        (-88,  45,  0.45),  # noqa
        ( 88,  45,  0.45),  # noqa
        (  0, -90,  -0.9),  # noqa
        (-88, -45, -0.45),  # noqa
        ( 88, -45, -0.45),  # noqa
        (  0,   0,     0),  # noqa
    ]

    points = [Point(*p) for p in points]

    diagonals = {
            'X': 246.650,
            'Y': 246.650,
            'Z': 246.650,
        }
    deltaRadius = 99.98
    homedHeight = 239.99
    bedRadius = 100
    towerAngCorr = {
        'X': 0.24,
        'Y': -0.24,
        'Z': 0,
    }
    endstopCorr = {
        'X': -0.49,
        'Y': -0.49,
        'Z': 0.98,
    }
    bedTilt = {
        'X': 0,
        'Y': 0,
    }

    result = Escher(dp, points, factorsNumber)
    print(result.toString())

    assert result.diagonals == diagonals
    assert result.deltaRadius == deltaRadius
    assert result.homedHeight == homedHeight
    assert result.bedRadius == bedRadius
    assert result.towerAngCorr == towerAngCorr
    assert result.endstopCorr == endstopCorr
    assert result.bedTilt == bedTilt


def test_Escher_7_factors():
    factorsNumber = 7

    dp = DeltaParams()
    print(dp.toString())

    points = [
        (  0,  90,   0.9),  # noqa
        (-88,  45,  0.45),  # noqa
        ( 88,  45,  0.45),  # noqa
        (  0, -90,  -0.9),  # noqa
        (-88, -45, -0.45),  # noqa
        ( 88, -45, -0.45),  # noqa
        (  0,   0,     0),  # noqa
    ]

    points = [Point(*p) for p in points]

    diagonals = {
            'X': 247.790,
            'Y': 247.790,
            'Z': 247.790,
        }
    deltaRadius = 100.25
    homedHeight = 239.99
    bedRadius = 100
    towerAngCorr = {
        'X': 0.23,
        'Y': -0.23,
        'Z': 0,
    }
    endstopCorr = {
        'X': -0.49,
        'Y': -0.49,
        'Z': 0.98,
    }
    bedTilt = {
        'X': 0,
        'Y': 0,
    }

    result = Escher(dp, points, factorsNumber)
    print(result.toString())

    assert result.diagonals == diagonals
    assert result.deltaRadius == deltaRadius
    assert result.homedHeight == homedHeight
    assert result.bedRadius == bedRadius
    assert result.towerAngCorr == towerAngCorr
    assert result.endstopCorr == endstopCorr
    assert result.bedTilt == bedTilt


test_Escher_6_factors()
test_Escher_7_factors()
