from __future__ import annotations
from typing import List, Optional, Tuple, Union, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from custom_qt_classes.plot_data_item import CustomPlotDataItem
    from pyqtgraph import LabelItem

import pyqtgraph as pg
from datetime import datetime
from pyqtgraph.graphicsItems.LegendItem import LegendItem, ItemSample
import utils
from PySide6 import QtCore
import math

class DateAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableAutoSIPrefix(False)
        self.num_ticks=7

    def tickValues(self, minVal, maxVal, size):
        if maxVal == minVal:
            return []
        step = (maxVal - minVal) /self.num_ticks
        majorTicks = [minVal + i * step for i in range(self.num_ticks+1)]
        return [(step, majorTicks)]
        
    def tickStrings(self, values, scale, spacing):
        try:
            if values[-1] - values[0] >= 3600*24:
                return [datetime.fromtimestamp(val).strftime("%d-%H:%M") for val in values]
            elif values[-1] - values[0] > len(values)*60:
                return [datetime.fromtimestamp(val).strftime("%H:%M") for val in values]
            elif len(values)/60/600 < (values[-1] - values[0]) < len(values)*60:
                return [datetime.fromtimestamp(val).strftime("%H:%M:%S") for val in values]
            else:
                return [datetime.fromtimestamp(val).strftime("%H:%M:%S.%f") for val in values]
        except:
            return [str(val) for val in values]

class CustomPriceAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableAutoSIPrefix(False)
        self.num_ticks=7

    def tickValues(self, minVal, maxVal, size):
        if maxVal == minVal:
            return []
        step = (maxVal - minVal) / self.num_ticks
        majorTicks = [minVal + i * step for i in range(self.num_ticks+1)]
        return [(step, majorTicks)]
            
    def tickStrings(self, values, scale, spacing):

        diff = abs(values[1] - values[0])

        if diff <= 0:
            precision = 6 
        else:
            precision = max(0, -int(math.floor(math.log10(diff))) + 1)

        return [f"{val:.{precision}f}" for val in values]

class NoSymbolItemSample(ItemSample):
    def __init__(self, instrument_name, item, *args, **kwargs):
        super().__init__(item, *args, **kwargs)
        self.instrument_name = instrument_name

    def paint(self, p, *args):
        if isinstance(self.item, pg.PlotDataItem):
            opts = self.item.opts
            pen  = opts.get('pen', None)
            if pen is not None:
                p.setPen(pen)
                r = self.boundingRect()
                y = r.center().y()
                p.drawLine(r.left(), y, r.right(), y)


class CustomLegend(LegendItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.legend_width=None
        self.legend_x_coord=None
        self.temp_item_name=[]
        self._itemToLabelMap: Dict[CustomPlotDataItem, LabelItem] = {}
        self._itemToSampleMap: Dict[CustomPlotDataItem, NoSymbolItemSample] = {}
        self.used_colours=[]
        self._block_updates=False

    def addItem(self, plot_data_item: CustomPlotDataItem, *args, **kwargs):
        if not plot_data_item in self._itemToLabelMap:
            price = plot_data_item.major_value
            sample = NoSymbolItemSample(plot_data_item.name(), plot_data_item)
            labelText = f"{plot_data_item.name()}: {utils.format_price(price)}"
            label = pg.LabelItem(labelText, color=plot_data_item.current_color)
            
            if not plot_data_item.current_color in self.used_colours:
                self.used_colours.append(plot_data_item.current_color)
            
            plot_data_item.sigVisibilityChanged.connect(self._updateItemVisibility)
            plot_data_item.sigPlotChanged.connect(self.setItemLastValue)
            plot_data_item.legend_label=label
            if hasattr(plot_data_item, "color_changed"):
                plot_data_item.color_changed.connect(self.update_color)
            
            row = len(self.items)
            self.items.append((sample, label))
            self.layout.addItem(label, row, 1)

            self._itemToLabelMap[plot_data_item] = label
            self._itemToSampleMap[plot_data_item] = sample
            self.temp_item_name.append(plot_data_item.name())
            self._calculate_width()
    
    def block_updates(self, flag):
        self._block_updates=flag
    
    def setText(self,
                value: float,
                item: CustomPlotDataItem
                ) -> None:
        if item in self._itemToLabelMap and item in self._itemToSampleMap:
            label = self._itemToLabelMap[item]
            sample = self._itemToSampleMap[item]
            instrument_name = sample.instrument_name  
            text = f"{instrument_name}: {utils.format_price(value)}"
            if not item.minor_value is None:
                if item.minor_value < 0:
                    minor_str = f"({item.minor_value:.2f})"
                else:
                    minor_str = f"({item.minor_value:.2g})"
                text = text + f" {minor_str}"
            label.setText(text)
        self._calculate_width()
    
    def setItemLastValue(self,
                         item: CustomPlotDataItem
                         ) -> None:
        if self._block_updates:
            return 
        newPrice = item.major_value
        if item in self._itemToLabelMap and item in self._itemToSampleMap:
            label = self._itemToLabelMap[item]
            sample = self._itemToSampleMap[item]
            instrument_name = sample.instrument_name  
            text = f"{instrument_name}: {utils.format_price(newPrice)}"
            if not item.minor_value is None:
                if item.minor_value < 0:
                    minor_str = f"({item.minor_value:.2f})"
                else:
                    minor_str = f"({item.minor_value:.2g})"
                text = text + f" {minor_str}"

            label.setText(text)
        self._calculate_width()

    def update_color(self,
                     item: CustomPlotDataItem
                     ) -> None:
        label = self._itemToLabelMap[item]
        label.setAttr("color", item.current_color)
        label.update()
        
    def _calculate_width(self):
        local_rect = self.boundingRect()
        scene_rect = self.mapRectToScene(local_rect)

        if scene_rect.width() == 0 or scene_rect.height() == 0:
            return  
        tl_data = self.parentItem().mapSceneToView(scene_rect.topLeft())      
        
        tr_data = self.parentItem().mapSceneToView(scene_rect.topRight())   

        self.legend_x_coord = tl_data.x()
        self.legend_width = tr_data.x() - tl_data.x() 

    @QtCore.Slot(object)
    def _updateItemVisibility(self,
                              item: CustomPlotDataItem
                              ) -> None:
        if item in self._itemToLabelMap and item in self._itemToSampleMap:
            visible = item.isVisible()
            self._itemToLabelMap[item].setVisible(visible)
            self._itemToSampleMap[item].setVisible(visible)
            vis=0
            for item in self._itemToLabelMap.values():
                if item.isVisible():
                    vis+=1
            self.updateSize()

    def updateSize(self):
        if self.size is not None:
            return
        height = 0
        width = 0
        for row in range(self.layout.rowCount()):
            row_height = 0
            col_width = 0
            for col in range(self.layout.columnCount()):
                item = self.layout.itemAt(row, col) 
                if item:
                    if item.isVisible():
                        col_width += item.width() + 3
                        row_height = max(row_height, item.height())
            width = max(width, col_width)
            height += row_height
        self.setGeometry(0, 0, width, height)
        return
    
    
class MedianLegend(LegendItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.legend_width=None
        self.legend_x_coord=None
        self._nameToLabelMap = {}
        self.temp_item_name=[]
        self._itemToSampleMap = {}
        self.used_colours=[]

    def addItem(self, plot_data_item: pg.ScatterPlotItem, *args, **kwargs):
        price = plot_data_item.median
        sample = NoSymbolItemSample(plot_data_item.name(), plot_data_item)
        labelText = f"{plot_data_item.name()} weight: {utils.format_price(price)}"
        label = pg.LabelItem(labelText, color=plot_data_item.color)
        
        row = len(self.items)
        self.items.append((sample, label))
        self.layout.addItem(label, row, 1)
        
        plot_data_item.sigPlotChanged.connect(self.setItemLastValue)
        
        self._nameToLabelMap[plot_data_item.name()] = label
        self._itemToSampleMap[plot_data_item.name()] = sample
        self.temp_item_name.append(plot_data_item.name())

    
    def setText(self, value: float, item: pg.ScatterPlotItem):
        if item.name() in self._nameToLabelMap and item.name() in self._itemToSampleMap:
            label = self._nameToLabelMap[item.name()]
            sample = self._itemToSampleMap[item.name()]
            instrument_name = sample.instrument_name  
            label.setText(f"{instrument_name}: {round(value,1)}%")
    
    def setItemLastValue(self, item: pg.ScatterPlotItem):
        new_median = item.median
        label = self._nameToLabelMap[item.name()]
        sample = self._itemToSampleMap[item.name()]
        instrument_name = sample.instrument_name  
        label.setText(f"{instrument_name} weight: {round(new_median, 1)}%")
        self.update()


    def update_color(self, item):
        label = self._nameToLabelMap[item]
        label.setAttr("color", item.current_color)
        label.update()
        
    def _updateItemVisibility(self, item):
        if item in self._nameToLabelMap and item in self._itemToSampleMap:
            visible = item.isVisible()
            self._nameToLabelMap[item].setVisible(visible)
            self._itemToSampleMap[item].setVisible(visible)
            vis=0
            for item in self._nameToLabelMap.values():
                if item.isVisible():
                    vis+=1
            self.updateSize()

    def updateSize(self):
        if self.size is not None:
            return
        height = 0
        width = 0
        for row in range(self.layout.rowCount()):
            row_height = 0
            col_width = 0
            for col in range(self.layout.columnCount()):
                item = self.layout.itemAt(row, col) 
                if item:
                    if item.isVisible():
                        col_width += item.width() + 3
                        row_height = max(row_height, item.height())
            width = max(width, col_width)
            height += row_height
        self.setGeometry(0, 0, width, height)
        return
