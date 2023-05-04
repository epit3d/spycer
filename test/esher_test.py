
from src.esher import DeltaParams, Esher, Point

def test_Esher():
    dp = DeltaParams(
        bedRadius=100.0,
        deltaRadius=200.0,
        homedHeight=300.0,
        diagonalRodLength=400.0,
        deltaHeight=500.0,
        towerPosition=[600.0, 700.0, 800.0],
        diagonalCorrection=[1.0, 1.0, 1.0],
    )
    points = [
        Point(X=0.0, Y=0.0, Z=100.0),
        Point(X=0.0, Y=100.0, Z=0.0),
        Point(X=100.0, Y=0.0, Z=0.0),
        Point(X=0.0, Y=0.0, Z=200.0),
        Point(X=0.0, Y=200.0, Z=0.0),
        Point(X=200.0, Y=0.0, Z=0.0),
    ]
    factorsNumber = 6
    expected_dp = DeltaParams(
        bedRadius=100.0,
        deltaRadius=200.0,
        homedHeight=300.0,
        diagonalRodLength=400.0,
        deltaHeight=500.0,
        towerPosition=[625.509375, 725.509375, 825.509375],
        diagonalCorrection=[0.9835944548853724, 0.9835944548853724, 0.9835944548853724],
    )
    assert Esher(dp, points, factorsNumber) == expected_dp

def test_Esher_with_new_DeltaParams():
    dp = DeltaParams()
    dp.diagonals = {
        'X': 240.0,
        'Y': 240.0,
        'Z': 240.0,
    }
    dp.deltaRadius = 120
    dp.homedHeight = 250
    dp.bedRadius = 110
    dp.towerAngCorr = {
        'X': -0.3,
        'Y': 0.2,
        'Z': 0.1,
    }
    dp.endstopCorr = {
        'X': 0.0,
        'Y': 0.0,
        'Z': 0.0,
    }
    dp.bedTilt = {
        'X': 0.5,
        'Y': -0.2,
    }

    points = [        Point(10, 10, 230),        Point(20, -10, 240),        Point(-10, -20, 245),    ]

    factorsNumber = 6
    result = Esher(dp, points, factorsNumber)

    expected_diagonals = {
        'X': 239.21455328499772,
        'Y': 239.21455328499772,
        'Z': 239.21455328499772,
    }
    expected_towerPosition = {
        'X': -0.05422587455367861,
        'Y': 0.009318861221328773,
        'Z': -0.027253142937266164,
    }

    assert result.diagonals == expected_diagonals
    assert result.towerPosition == expected_towerPosition
        
test_Esher()
test_Esher_with_new_DeltaParams()