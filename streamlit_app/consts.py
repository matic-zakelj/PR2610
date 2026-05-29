import matplotlib.pyplot as plt

DRIVERS = None
COMPOUND_COLORS = {
    'SOFT':   '#E12319',
    'MEDIUM': '#FFEF00',
    'HARD':   '#FFFFFF',
    'INTERMEDIATE':  '#39B54A',
    'WET':    '#0067FF',
}
PRIMARY_TYRES = ['SOFT', 'MEDIUM', 'HARD']
ALL_TYRES = ['SOFT','MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']
DRY_LAPS_ONLY = True # ali zelimo primerjati samo suhe ali pa vse
CHOSEN_TYRES = (PRIMARY_TYRES if DRY_LAPS_ONLY else ALL_TYRES)
COLORS = plt.cm.tab20.colors
MIN_LAPS_FOR_FIT = 5    # najmanjše število krogov za regresijsko premico
