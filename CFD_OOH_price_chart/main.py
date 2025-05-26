#%%
from __future__ import annotations

from streaming import synthetic_client
from timeseries import builders as builders_timeseries
from historical import utils as utils_historical
from instruments import builders as builders_instruments

from exchanges import builders as exchanges_utils
from subplot_structure import config as subplot_structure_config
from subplot_structure import builders as builders_subplot_structure
from custom_qt_classes import builders as builders_custom_qt_classes
import streaming.ig_client as ig_client
import application
from queue import Queue
import workers
import sys
from ig_measuring import builders as builders_ig_measuring
from ig_measuring import config as config_ig_measuring


def main():
    
    """
    if you want real, you have to change the delay in /time_helpers/classes
    """
    test_flag=True
    
    
    
    ig_measure=True
    
    
    
    
    plot_configurations, instrument_container = subplot_structure_config.get_config()

    exchange_container = exchanges_utils.create_exchange_objects()
    
    instrument_specs = builders_instruments.create_instrument_spec_dataclasses(instrument_container, exchange_container)
    instrument_info_container = builders_instruments.create_instrument_info_classes(instrument_specs)
    
    df_dict = utils_historical.get_historical_data(instrument_container, test_flag)

    timeseries_parent_container = builders_timeseries.create_parent_timeseries_container(instrument_container, df_dict)
    
    instrument_container = builders_instruments.create_instrument_objects_objects(instrument_container,
                                                                                  timeseries_parent_container,
                                                                                  instrument_specs,
                                                                                  instrument_info_container
                                                                                  )
    
    
    
    subplot_structure_container = builders_subplot_structure.create_subplot_structure_containers(plot_configurations,
                                                                                                 timeseries_parent_container,
                                                                                                 instrument_container,
                                                                                                 )

    if ig_measure:
        ig_measuring_configs = config_ig_measuring.get_config()
        builders_ig_measuring.create_weight_metrics(subplot_structure_container,
                                                    ig_measuring_configs)
        
    queue = Queue()
    if test_flag:
        streaming_client = synthetic_client.create_streaming_application(instrument_container, queue)
    else:
        streaming_client = ig_client.create_streaming_application(instrument_container, queue)
    
    app = application.Application(sys.argv)

    subplot_widget_container = builders_custom_qt_classes.create_subplot_widget_container(subplot_structure_container)
    builders_custom_qt_classes.add_data_to_subplots(subplot_widget_container)
    
    app.add_subplot_widgets(subplot_widget_container)
    
    app.add_data(instrument_container,
                 timeseries_parent_container,
                 exchange_container)
    websocket_worker = workers.WebsocketWorker(queue=queue)
    app.add_streaming_apps(websocket_worker, streaming_client)
    app.start()
    
    
    sys.exit(app.exec())
    

    
    
if __name__ == "__main__":
    main()
