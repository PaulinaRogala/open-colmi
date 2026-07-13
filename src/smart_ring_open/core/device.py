from abc import ABC, abstractmethod

class RingDevice(ABC):
    """Common interface for every smart ring"""
    @abstractmethod
    def connect(self)->bool:
        """Connect with the device."""
        pass
    @abstractmethod
    def disconnect(self)->bool:
        """Disconnect from the device."""
        pass
    @abstractmethod
    def is_connected(self)->bool:
        """Check if the device is connected."""
        pass
    @abstractmethod
    def get_sensor_data(self)->dict[str, Any]:
        """Get data from sensors."""
        pass
    @abstractmethod
    def get_battery_level(self)->int|None:
        """(optional)Get the device battery level."""
        pass
    
