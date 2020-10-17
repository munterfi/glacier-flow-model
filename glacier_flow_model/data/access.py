from glacier_flow_model.base import Base
from osgeo.gdal import Open, Dataset
import importlib.resources as resources


class PkgDataAccess(Base):
    """Package example data bindings."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initializes an instance of the PkgDataAccess class.

        Parameters
        ----------
        verbose : bool
            Should information be printed?

        Returns
        -------
        None
            Constructor of the PkgDataAccess class.

        """
        super().__init__(verbose)
        self.verbose = verbose

    def locate_dem(self) -> str:
        """
        Locates the file 'dem.tif' on the current system.

        Returns
        -------
        str
            The path to the file on the system.

        """
        with resources.path('glacier_flow_model.data', 'dem.tif') as file_path:
            self._print(f"Example located at '{file_path}' ...")
            return str(file_path)

    def load_dem(self) -> Dataset:
        """
        Loads the file 'dem.tif' on the current system.

        Returns
        -------
        Dataset
            The example digital elevation model.

        """
        file_path = self.locate_dem()
        self._print(f"Reading example from '{file_path}' ...")
        dem = Open(file_path)
        return dem
