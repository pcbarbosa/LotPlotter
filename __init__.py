def classFactory(iface):
    from .lot_plotter import LotPlotter
    return LotPlotter(iface)
