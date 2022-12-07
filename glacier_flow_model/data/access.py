"""Helper for example data access, shipped with the package."""
import importlib.resources as resources
from logging import getLogger

from rasterio import open
from rasterio import DatasetReader

LOG = getLogger(__name__)


class PkgDataAccess:
    """Package example data bindings."""

    def __init__(self) -> None:
        """
        Initializes an instance of the PkgDataAccess class.

        Returns
        -------
        None
            Constructor of the PkgDataAccess class.

        """
        pass

    @staticmethod
    def locate_dem() -> str:
        """
        Locates the file 'dem.tif' on the current system.

        Returns
        -------
        str
            The path to the file on the system.

        """
        with resources.path("glacier_flow_model.data", "aletsch.tif") as file_path:
            LOG.info("Example DEM at '%s' ...", file_path)
            return str(file_path)

    @staticmethod
    def load_dem() -> DatasetReader:
        """
        Loads the file 'dem.tif' on the current system.

        Returns
        -------
        Dataset
            The example digital elevation model.

        """
        file_path = PkgDataAccess.locate_dem()
        LOG.info("Reading DEM from '%s' ...", file_path)
        dem = open(file_path)
        return dem
