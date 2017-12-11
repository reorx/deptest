from deptest.log import color


def test_red():
    print('white', color.dye('red', 'its red'), 'white')


def test_green():
    print('white', color.dye('green', 'its green'), 'white')


def test_blue():
    print('white', color.dye('blue', 'its blue'), 'white')


def test_yellow():
    print('white', color.dye('yellow', 'its yellow'), 'white')
