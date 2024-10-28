"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-30 15:44:29
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-30 15:44:41
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_source.py
Description: 
"""


class CustomDataSource:
    """
    This part is for selfmade data source, you need to implement the functions below.
    Here is an example when you use your own data_source:
        class MyDataSource(CustomDataSource):
            def __init__(self):
                super().__init__()
            def read_ts_xrdataset(self):
                ...
            def read_attr_xrdataset(self):
                ...
            def read_mean_prcp(self):
                ...
            def other_function(self):
                <if you need>
        data_source = CustomDataSource()
        eval_deep_hydro = EvalDeepHydro(DEFAULT_cfgs, data_source=data_source)
        eval_deep_hydro.model_infer()
    """

    def __init__(self):
        pass

    def read_ts_xrdataset(self, gage_id_lst, t_range, var_lst, time_units):
        """
        Returns a dictionary with time units as keys and xarray.Dataset as values.

        The structure of the returned dictionary is similar to below:

        {
            'time_unit': <xarray.Dataset>,
            ...
        }

        - 'time_unit': A string representing the time interval (e.g., '3h', '1h').
        - <xarray.Dataset>: An xarray Dataset object with the following structure:
            - Dimensions:
                * basin: represents different basin IDs (e.g., 'AAAA').
                * time: represents time steps, typically datetime64 format.
            - Coordinates:
                * basin (basin): A list of basin identifiers.
                * time (time): A list of time values in datetime64[ns].
            - Data variables:
                * total_precipitation_hourly (basin, time)
                * precipitationCal (basin, time)
                * hourly_precipitation (basin, time)
                * sm_surface (basin, time)

        Example of a dataset within the dictionary:

        <xarray.Dataset>
        Dimensions:  (basin: 2, time: 490)
        Coordinates:
        * basin    (basin) <U17 'AAAA' 'BBBB'
        * time     (time) datetime64[ns] 2015-06-01T01:00:00 2015-06-01T04:00:00 ... 2015-06-01T10:00:00
        Data variables:
            total_precipitation_hourly  (basin, time) float64 0.01 ... 0.4
            precipitationCal            (basin, time) float64 0.01 ... 0.4
            hourly_precipitation        (basin, time) float64 0.01 ... 0.4
            sm_surface                  (basin, time) float64 0.01 ... 0.4

        Returns:
            dict: A dictionary where the keys are time intervals (e.g., '3h') and values are xarray.Dataset objects.
        """
        raise NotImplementedError

    def read_attr_xrdataset(self, gage_id_lst, var_lst):
        """
        Returns an xarray.Dataset with basin-level variables.

        The dataset contains the following structure:

        - Dimensions:
        * basin: Represents the basin identifiers, with a total of 2 basins. The basin identifiers are strings up to 25 characters long (e.g., 'songliao_21401050', 'songliao_21401550').

        - Coordinates:
        * basin (basin): A list of basin identifiers, represented as strings with a maximum length of 25 characters.

        - Data variables:
        * area (basin): The area of each basin, represented as float64.
        ...

        Returns:
            xarray.Dataset: A dataset containing basin-level environmental and geographical variables.
        """
        raise NotImplementedError

    def read_mean_prcp(self, gage_id_lst):
        """
        the pre_mm_syr variable in attr

        <xarray.Dataset> Size: 216B
        Dimensions:     (basin: 2)
        Coordinates:
        * basin       (basin) <U25 200B 'AAAA' 'BBBB'
        Data variables:
            pre_mm_syr  (basin) float64 16B ...
        """
        # return self.read_attr_xrdataset(gage_id_lst, ["pre_mm_syr"])
        raise NotImplementedError


class CustomDataSourceForHydroModel:
    """
    For Xaj Model
    """

    def __init__(self):
        pass

    def get_p_and_e_dict(self, gage_id_lst):
        raise NotImplementedError

    def get_area_dict(self, gage_id_lst):
        raise NotImplementedError
